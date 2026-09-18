#include "kernel/yosys.h"
#include "kernel/sigtools.h"

USING_YOSYS_NAMESPACE
PRIVATE_NAMESPACE_BEGIN


struct SelectorCondition
{
    bool valid = false;
    RTLIL::SigSpec signal;
    RTLIL::Const value;
};


struct PmuxInfo
{
    RTLIL::Cell *cell = nullptr;

    int width = 0;
    int s_width = 0;
    int ctrl_width = 0;

    RTLIL::SigSpec port_a;
    RTLIL::SigSpec port_b;
    RTLIL::SigSpec port_s;
    RTLIL::SigSpec port_y;

    RTLIL::SigSpec control;

    std::vector<SelectorCondition> conditions;

    bool selector_bank_valid = false;
    bool full_decode = false;

    // control value -> 原 PMUX branch index
    std::vector<int> branch_for_value;
};


struct PairSwapCandidate
{
    // members[] 中的下标
    int member_a = -1;
    int member_b = -1;

    int swap_bit = -1;
    int swapped_pairs = 0;

    // swap_bit=0 一侧不满足 pair-swap 的状态
    std::vector<int> special_base_values;
};


struct PmuxOptPass : public Pass
{
    PmuxOptPass()
        : Pass(
            "pmux_opt",
            "optimize shared-selector PMUX pair-swap structures")
    {
    }


    void help() override
    {
        log("\n");
        log("    pmux_opt [selection]\n");
        log("\n");
        log("Detect shared-selector $pmux groups and optimize\n");
        log("pair-swap structures across two PMUX cells.\n");
        log("\n");
        log("Recommended flow:\n");
        log("    proc\n");
        log("    opt\n");
        log("    pmux_opt\n");
        log("\n");
    }


    void execute(
        std::vector<std::string> args,
        RTLIL::Design *design) override
    {
        log_header(
            design,
            "Executing PMUX_OPT pair-swap optimization.\n");

        extra_args(args, 1, design);

        int total_pmux = 0;
        int total_groups = 0;
        int total_pair_candidates = 0;
        int total_pair_rebuilt = 0;


        for (auto module : design->selected_modules())
        {
            SigMap sigmap(module);

            /*
             * ==================================================
             * 建立：
             *
             * signal bit -> driver cell
             * ==================================================
             */
            dict<RTLIL::SigBit, RTLIL::Cell *> driver_map;

            for (auto driver_cell : module->cells())
            {
                for (auto &conn :
                     driver_cell->connections())
                {
                    if (!driver_cell->output(conn.first))
                        continue;

                    RTLIL::SigSpec output =
                        sigmap(conn.second);

                    for (auto bit : output)
                        driver_map[bit] =
                            driver_cell;
                }
            }


            /*
             * ==================================================
             * 第一部分
             *
             * 分析每一个 $pmux
             * ==================================================
             */
            std::vector<PmuxInfo> pmux_infos;

            for (auto cell : module->selected_cells())
            {
                if (cell->type != ID($pmux))
                    continue;

                total_pmux++;

                PmuxInfo info;

                info.cell = cell;

                info.width =
                    cell->getParam(ID::WIDTH).as_int();

                info.s_width =
                    cell->getParam(ID::S_WIDTH).as_int();

                info.port_a =
                    cell->getPort(ID::A);

                info.port_b =
                    cell->getPort(ID::B);

                info.port_s =
                    cell->getPort(ID::S);

                info.port_y =
                    cell->getPort(ID::Y);

                info.conditions.resize(
                    info.s_width);


                /*
                 * ----------------------------------------------
                 * 解析每个 S[i]
                 * ----------------------------------------------
                 */
                for (int i = 0;
                     i < info.s_width;
                     i++)
                {
                    RTLIL::SigSpec s_bit =
                        sigmap(
                            info.port_s.extract(
                                i,
                                1));

                    if (s_bit.size() != 1)
                        continue;

                    auto it =
                        driver_map.find(
                            s_bit.as_bit());

                    if (it == driver_map.end())
                        continue;

                    RTLIL::Cell *driver =
                        it->second;


                    /*
                     * selector = control == constant
                     */
                    if (driver->type == ID($eq))
                    {
                        RTLIL::SigSpec cond_a =
                            sigmap(
                                driver->getPort(ID::A));

                        RTLIL::SigSpec cond_b =
                            sigmap(
                                driver->getPort(ID::B));


                        if (!cond_a.is_fully_const() &&
                            cond_b.is_fully_const())
                        {
                            info.conditions[i].valid =
                                true;

                            info.conditions[i].signal =
                                cond_a;

                            info.conditions[i].value =
                                cond_b.as_const();
                        }
                        else if (
                            cond_a.is_fully_const() &&
                            !cond_b.is_fully_const())
                        {
                            info.conditions[i].valid =
                                true;

                            info.conditions[i].signal =
                                cond_b;

                            info.conditions[i].value =
                                cond_a.as_const();
                        }
                    }


                    /*
                     * selector = !control
                     *
                     * 多位 control 时：
                     *
                     * !control
                     *
                     * 等价于：
                     *
                     * control == 0
                     */
                    else if (
                        driver->type ==
                        ID($logic_not))
                    {
                        RTLIL::SigSpec cond_a =
                            sigmap(
                                driver->getPort(ID::A));

                        if (!cond_a.is_fully_const())
                        {
                            info.conditions[i].valid =
                                true;

                            info.conditions[i].signal =
                                cond_a;

                            info.conditions[i].value =
                                RTLIL::Const(
                                    0,
                                    cond_a.size());
                        }
                    }
                }


                /*
                 * ----------------------------------------------
                 * 所有 selector 必须来自同一个 control
                 * ----------------------------------------------
                 */
                bool valid = true;
                bool first = true;

                for (int i = 0;
                     i < info.s_width;
                     i++)
                {
                    const auto &cond =
                        info.conditions[i];

                    if (!cond.valid)
                    {
                        valid = false;
                        break;
                    }

                    if (first)
                    {
                        info.control =
                            cond.signal;

                        first = false;
                    }
                    else if (
                        cond.signal !=
                        info.control)
                    {
                        valid = false;
                        break;
                    }

                    if (cond.value.size() !=
                        info.control.size())
                    {
                        valid = false;
                        break;
                    }
                }

                info.selector_bank_valid =
                    valid;

                if (valid)
                    info.ctrl_width =
                        info.control.size();


                /*
                 * ----------------------------------------------
                 * 判断是否完整覆盖：
                 *
                 * 0 ... 2^k - 1
                 * ----------------------------------------------
                 */
                if (valid &&
                    info.ctrl_width > 0 &&
                    info.ctrl_width < 31)
                {
                    int expected_choices =
                        1 << info.ctrl_width;

                    if (info.s_width ==
                        expected_choices)
                    {
                        info.branch_for_value.assign(
                            expected_choices,
                            -1);

                        bool full = true;

                        for (int branch = 0;
                             branch <
                             info.s_width;
                             branch++)
                        {
                            bool matched = false;

                            for (int value = 0;
                                 value <
                                 expected_choices;
                                 value++)
                            {
                                RTLIL::Const
                                    expected_value(
                                        value,
                                        info.ctrl_width);

                                if (info.
                                        conditions[branch].
                                        value ==
                                    expected_value)
                                {
                                    if (info.
                                            branch_for_value[
                                                value] !=
                                        -1)
                                    {
                                        full = false;
                                        break;
                                    }

                                    info.
                                        branch_for_value[
                                            value] =
                                        branch;

                                    matched = true;
                                    break;
                                }
                            }

                            if (!matched)
                            {
                                full = false;
                                break;
                            }

                            if (!full)
                                break;
                        }


                        if (full)
                        {
                            for (int value = 0;
                                 value <
                                 expected_choices;
                                 value++)
                            {
                                if (info.
                                        branch_for_value[
                                            value] ==
                                    -1)
                                {
                                    full = false;
                                    break;
                                }
                            }
                        }

                        info.full_decode =
                            full;
                    }
                }


                pmux_infos.push_back(
                    info);
            }


            /*
             * ==================================================
             * 第二部分
             *
             * 找 shared-selector group
             * ==================================================
             */
            std::vector<bool> grouped(
                pmux_infos.size(),
                false);

            for (int i = 0;
                 i < int(pmux_infos.size());
                 i++)
            {
                if (grouped[i])
                    continue;

                if (!pmux_infos[i].
                        selector_bank_valid ||
                    !pmux_infos[i].
                        full_decode)
                    continue;


                std::vector<int> members;

                members.push_back(i);


                for (int j = i + 1;
                     j < int(pmux_infos.size());
                     j++)
                {
                    if (grouped[j])
                        continue;

                    if (!pmux_infos[j].
                            selector_bank_valid ||
                        !pmux_infos[j].
                            full_decode)
                        continue;

                    if (pmux_infos[j].
                            ctrl_width !=
                        pmux_infos[i].
                            ctrl_width)
                        continue;

                    if (pmux_infos[j].
                            control !=
                        pmux_infos[i].
                            control)
                        continue;

                    members.push_back(j);
                }


                if (members.size() < 2)
                    continue;


                for (int index : members)
                    grouped[index] = true;


                total_groups++;

                auto &base =
                    pmux_infos[
                        members[0]];

                int choices =
                    1 << base.ctrl_width;

                int pair_count =
                    choices / 2;


                log("\n");
                log(
                    "========================================\n");

                log(
                    "SHARED SELECTOR GROUP %d\n",
                    total_groups);

                log(
                    "  control    : %s\n",
                    log_signal(
                        base.control));

                log(
                    "  ctrl_width : %d\n",
                    base.ctrl_width);

                log(
                    "  choices    : %d\n",
                    choices);

                log(
                    "  members    : %zu\n",
                    members.size());


                for (int m = 0;
                     m <
                     int(members.size());
                     m++)
                {
                    auto &info =
                        pmux_infos[
                            members[m]];

                    log(
                        "    member[%d] : %s WIDTH=%d\n",
                        m,
                        log_id(info.cell),
                        info.width);
                }


                /*
                 * ==================================================
                 * 第三部分
                 *
                 * 找 pair-swap candidate
                 * ==================================================
                 */
                std::vector<PairSwapCandidate>
                    candidates;


                for (int a = 0;
                     a < int(members.size());
                     a++)
                {
                    for (int b = a + 1;
                         b <
                         int(members.size());
                         b++)
                    {
                        auto &info_a =
                            pmux_infos[
                                members[a]];

                        auto &info_b =
                            pmux_infos[
                                members[b]];


                        /*
                         * 目前只优化同宽 PMUX。
                         */
                        if (info_a.width !=
                            info_b.width)
                            continue;


                        /*
                         * 至少需要：
                         *
                         * control[0]
                         * +
                         * 一个更高位
                         */
                        if (base.ctrl_width < 2)
                            continue;


                        PairSwapCandidate best_candidate;
                        bool have_candidate = false;

                        for (int swap_bit_index = 0;
                             swap_bit_index < base.ctrl_width;
                             swap_bit_index++)
                        {
                            int swapped_pairs = 0;
                            std::vector<int> special_base_values;

                            for (int base_value = 0;
                                 base_value < choices;
                                 base_value++)
                            {
                                if ((base_value >> swap_bit_index) & 1)
                                    continue;

                                int mate_value =
                                    base_value |
                                    (1 << swap_bit_index);

                                int a_base_branch =
                                    info_a.branch_for_value[base_value];
                                int a_mate_branch =
                                    info_a.branch_for_value[mate_value];
                                int b_base_branch =
                                    info_b.branch_for_value[base_value];
                                int b_mate_branch =
                                    info_b.branch_for_value[mate_value];

                                RTLIL::SigSpec a_base =
                                    sigmap(info_a.port_b.extract(
                                        a_base_branch * info_a.width,
                                        info_a.width));

                                RTLIL::SigSpec a_mate =
                                    sigmap(info_a.port_b.extract(
                                        a_mate_branch * info_a.width,
                                        info_a.width));

                                RTLIL::SigSpec b_base =
                                    sigmap(info_b.port_b.extract(
                                        b_base_branch * info_b.width,
                                        info_b.width));

                                RTLIL::SigSpec b_mate =
                                    sigmap(info_b.port_b.extract(
                                        b_mate_branch * info_b.width,
                                        info_b.width));

                                if ((a_base == b_mate) &&
                                    (b_base == a_mate))
                                    swapped_pairs++;
                                else
                                    special_base_values.push_back(
                                        base_value);
                            }

                            bool profitable_pattern =
                                swapped_pairs >= 2 &&
                                swapped_pairs * 4 >=
                                    pair_count * 3 &&
                                special_base_values.size() <= 1;

                            if (!profitable_pattern)
                                continue;

                            bool better =
                                !have_candidate ||
                                swapped_pairs >
                                    best_candidate.swapped_pairs ||
                                (swapped_pairs ==
                                     best_candidate.swapped_pairs &&
                                 special_base_values.size() <
                                     best_candidate.
                                         special_base_values.size());

                            if (!better)
                                continue;

                            have_candidate = true;

                            best_candidate.member_a = a;
                            best_candidate.member_b = b;
                            best_candidate.swap_bit =
                                swap_bit_index;
                            best_candidate.swapped_pairs =
                                swapped_pairs;
                            best_candidate.special_base_values =
                                special_base_values;
                        }

                        if (!have_candidate)
                            continue;

                        candidates.push_back(best_candidate);
                        total_pair_candidates++;

                        log("\n");
                        log("PAIR-SWAP CANDIDATE\n");
                        log("  A             : %s\n",
                            log_id(info_a.cell));
                        log("  B             : %s\n",
                            log_id(info_b.cell));
                        log("  data_width    : %d\n",
                            info_a.width);
                        log("  swap_bit      : control[%d]\n",
                            best_candidate.swap_bit);
                        log("  swapped_pairs : %d / %d\n",
                            best_candidate.swapped_pairs,
                            pair_count);
                        log("  special_pairs : %zu\n",
                            best_candidate.
                                special_base_values.size());
                    }
                }


                /*
                 * ==================================================
                 * 第四部分
                 *
                 * 真正执行 pair-swap rebuilding
                 * ==================================================
                 *
                 * 同一个 PMUX 一次只能参加一个 pair。
                 */
                std::vector<bool> member_used(
                    members.size(),
                    false);


                for (const auto &candidate :
                     candidates)
                {
                    int a =
                        candidate.member_a;

                    int b =
                        candidate.member_b;


                    if (member_used[a] ||
                        member_used[b])
                        continue;


                    auto &info_a =
                        pmux_infos[
                            members[a]];

                    auto &info_b =
                        pmux_infos[
                            members[b]];


                    int width =
                        info_a.width;


                    RTLIL::IdString
                        old_name_a =
                            info_a.cell->name;

                    RTLIL::IdString
                        old_name_b =
                            info_b.cell->name;


                    /*
                     * --------------------------------------------------
                     * helper 1
                     *
                     * 两根 selector 做 OR
                     *
                     * high_sel[p] =
                     * S[2p] | S[2p+1]
                     *
                     * 表示：
                     *
                     * control[高位] == p
                     * --------------------------------------------------
                     */
                    auto make_selector_or =
                        [&](RTLIL::SigSpec s0,
                            RTLIL::SigSpec s1)
                        -> RTLIL::SigSpec
                    {
                        RTLIL::SigSpec inputs;

                        inputs.append(s0);
                        inputs.append(s1);

                        RTLIL::Wire *wire =
                            module->addWire(
                                NEW_ID,
                                1);

                        RTLIL::Cell *cell =
                            module->addCell(
                                NEW_ID,
                                ID($reduce_or));

                        cell->setParam(
                            ID::A_SIGNED,
                            0);

                        cell->setParam(
                            ID::A_WIDTH,
                            2);

                        cell->setParam(
                            ID::Y_WIDTH,
                            1);

                        cell->setPort(
                            ID::A,
                            inputs);

                        cell->setPort(
                            ID::Y,
                            RTLIL::SigSpec(
                                wire));

                        return RTLIL::SigSpec(
                            wire);
                    };


                    /*
                     * --------------------------------------------------
                     * helper 2
                     *
                     * 创建普通 2:1 $mux
                     * --------------------------------------------------
                     */
                    auto make_mux =
                        [&](RTLIL::SigSpec in_a,
                            RTLIL::SigSpec in_b,
                            RTLIL::SigSpec select)
                        -> RTLIL::SigSpec
                    {
                        RTLIL::Wire *wire =
                            module->addWire(
                                NEW_ID,
                                width);

                        RTLIL::Cell *cell =
                            module->addCell(
                                NEW_ID,
                                ID($mux));

                        cell->setParam(
                            ID::WIDTH,
                            width);

                        cell->setPort(
                            ID::A,
                            in_a);

                        cell->setPort(
                            ID::B,
                            in_b);

                        cell->setPort(
                            ID::S,
                            select);

                        cell->setPort(
                            ID::Y,
                            RTLIL::SigSpec(
                                wire));

                        return RTLIL::SigSpec(
                            wire);
                    };


                    /*
                     * --------------------------------------------------
                     * helper 3
                     *
                     * 创建共享 selector 的 PMUX。
                     * --------------------------------------------------
                     */
                    auto make_pmux =
                        [&](RTLIL::SigSpec data_b,
                            RTLIL::SigSpec selectors)
                        -> RTLIL::SigSpec
                    {
                        RTLIL::Wire *wire =
                            module->addWire(
                                NEW_ID,
                                width);

                        RTLIL::Cell *cell =
                            module->addCell(
                                NEW_ID,
                                ID($pmux));

                        cell->setParam(
                            ID::WIDTH,
                            width);

                        cell->setParam(
                            ID::S_WIDTH,
                            selectors.size());

                        RTLIL::SigSpec undef_data =
                            RTLIL::Const(
                                State::Sx,
                                width);

                        cell->setPort(
                            ID::A,
                            undef_data);

                        cell->setPort(
                            ID::B,
                            data_b);

                        cell->setPort(
                            ID::S,
                            selectors);

                        cell->setPort(
                            ID::Y,
                            RTLIL::SigSpec(
                                wire));

                        return RTLIL::SigSpec(
                            wire);
                    };


                    /*
                     * ==================================================
                     * A/B 原来各自是 16 路。
                     *
                     * 现在先把：
                     *
                     * state 0/1
                     * state 2/3
                     * ...
                     *
                     * 合并成 8 组。
                     * ==================================================
                     */
                    RTLIL::SigSpec high_selectors;
                    RTLIL::SigSpec pair_x_data;
                    RTLIL::SigSpec pair_y_data;

                    for (int base_value = 0;
                         base_value < choices;
                         base_value++)
                    {
                        if ((base_value >>
                             candidate.swap_bit) & 1)
                            continue;

                        int mate_value =
                            base_value |
                            (1 << candidate.swap_bit);

                        int base_branch =
                            info_a.branch_for_value[
                                base_value];

                        int mate_branch =
                            info_a.branch_for_value[
                                mate_value];

                        RTLIL::SigSpec base_s =
                            info_a.port_s.extract(
                                base_branch, 1);

                        RTLIL::SigSpec mate_s =
                            info_a.port_s.extract(
                                mate_branch, 1);

                        bool special = false;

                        for (int v :
                             candidate.special_base_values)
                            if (v == base_value)
                                special = true;

                        if (special)
                        {
                            int a_base_branch =
                                info_a.branch_for_value[
                                    base_value];

                            int b_base_branch =
                                info_b.branch_for_value[
                                    base_value];

                            int a_mate_branch =
                                info_a.branch_for_value[
                                    mate_value];

                            int b_mate_branch =
                                info_b.branch_for_value[
                                    mate_value];

                            high_selectors.append(base_s);

                            pair_x_data.append(
                                info_a.port_b.extract(
                                    a_base_branch * width,
                                    width));

                            pair_y_data.append(
                                info_b.port_b.extract(
                                    b_base_branch * width,
                                    width));

                            high_selectors.append(mate_s);

                            pair_x_data.append(
                                info_b.port_b.extract(
                                    b_mate_branch * width,
                                    width));

                            pair_y_data.append(
                                info_a.port_b.extract(
                                    a_mate_branch * width,
                                    width));
                        }
                        else
                        {
                            high_selectors.append(
                                make_selector_or(
                                    base_s,
                                    mate_s));

                            int a_mate_branch =
                                info_a.branch_for_value[
                                    mate_value];

                            int b_mate_branch =
                                info_b.branch_for_value[
                                    mate_value];

                            pair_x_data.append(
                                info_b.port_b.extract(
                                    b_mate_branch * width,
                                    width));

                            pair_y_data.append(
                                info_a.port_b.extract(
                                    a_mate_branch * width,
                                    width));
                        }
                    }

                    RTLIL::SigSpec pair_x =
                        make_pmux(
                            pair_x_data,
                            high_selectors);

                    RTLIL::SigSpec pair_y =
                        make_pmux(
                            pair_y_data,
                            high_selectors);

                    RTLIL::SigSpec swap_bit =
                        info_a.control.extract(
                            candidate.swap_bit,
                            1);

                    RTLIL::SigSpec final_a =
                        make_mux(
                            pair_x,
                            pair_y,
                            swap_bit);

                    RTLIL::SigSpec final_b =
                        make_mux(
                            pair_y,
                            pair_x,
                            swap_bit);



                    /*
                     * 保存原输出。
                     */
                    RTLIL::SigSpec old_y_a =
                        info_a.port_y;

                    RTLIL::SigSpec old_y_b =
                        info_b.port_y;


                    /*
                     * 删除原来的两个大 PMUX。
                     */
                    module->remove(
                        info_a.cell);

                    module->remove(
                        info_b.cell);


                    /*
                     * 新结构接回原输出。
                     */
                    module->connect(
                        old_y_a,
                        final_a);

                    module->connect(
                        old_y_b,
                        final_b);


                    member_used[a] = true;
                    member_used[b] = true;

                    total_pair_rebuilt++;


                    log("\n");

                    log(
                        "PAIR-SWAP REBUILT\n");

                    log(
                        "  A          : %s\n",
                        log_id(old_name_a));

                    log(
                        "  B          : %s\n",
                        log_id(old_name_b));

                    log(
                        "  old choices: %d + %d\n",
                        choices,
                        choices);

                    log(
                        "  new pair choices: %d\n",
                        pair_count);

                    log(
                        "  swap bit   : control[%d]\n",
                        candidate.swap_bit);

                    log(
                        "  special    : %zu\n",
                        candidate.
                            special_base_values.
                            size());
                }


                log(
                    "========================================\n");
            }
        }


        log("\n");

        log(
            "Total $pmux cells: %d\n",
            total_pmux);

        log(
            "Total shared-selector groups: %d\n",
            total_groups);

        log(
            "Total pair-swap candidates: %d\n",
            total_pair_candidates);

        log(
            "Total pair-swap rebuilt: %d\n",
            total_pair_rebuilt);
    }
} PmuxOptPass;


PRIVATE_NAMESPACE_END