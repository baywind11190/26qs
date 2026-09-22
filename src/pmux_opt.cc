
/*
 * ================================================================
 * PMUX 优化算法统一编号
 *
 * 1 共享选择器换位优化
 *   1.1 共享选择器成对换位因式分解
 *   1.2 扩展共享选择器成对换位因式分解
 *
 * 2 条件传播优化
 *   2.1 分支控制位常量折叠
 *   2.2 选择条件驱动的表达式锥常量传播
 *
 * 3 条件约束比较器优化
 *   3.1 前置条件感知的比较器位宽缩减
 *
 * 4 分组轮换因式分解
 *   4.1 分组选择与四路循环轮换因式分解
 *
 * 5 优先级多路选择优化
 *   5.1 优先级多路选择链互斥选择因式分解
 *
 * 历史研发代号对应关系：
 *   Pattern A -> 1.1
 *   H1        -> 1.2
 *   Pattern B -> 2.1
 *   Pattern C -> 2.2
 *   Pattern D -> 3.1
 *   H2        -> 4.1
 *   H3        -> 5.1
 *
 * 说明：
 *   对外文档、报告和答辩统一使用上述中文编号与名称；
 *   历史研发代号仅用于兼容既有代码、日志和测试记录。
 * ================================================================
 */

#include "kernel/yosys.h"
#include "kernel/sigtools.h"
#include "kernel/consteval.h"

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

    // H2 four-lane cyclic rotation metadata.
    bool h2_rotation_candidate = false;
    int h2_lane_width = 0;
    int h2_bank_count = 0;

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


        int total_h3_candidates = 0;
        int total_h3_rebuilt = 0;
        for (auto module : design->selected_modules())
        {
            SigMap sigmap(module);

            /*
             * Pattern C 使用：
             * 在 selector 已知 control == CONST 的前提下，
             * 对 branch 数据锥进行条件常量传播。
             *
             * 其他未知输入统一视为 X。
             */
            ConstEval branch_consteval(
                module,
                RTLIL::State::Sx);

            /*
             * ==================================================
             * 建立：
             *
             * signal bit -> driver cell
             * ==================================================
             */
            dict<RTLIL::SigBit, RTLIL::Cell *> driver_map;

            // H2 safety only:
            // 记录 canonical bit 是否由多个不同 cell 驱动。
            // driver_map 本身仍保持原有行为，避免影响
            // Pattern A/B/C/D。
            pool<RTLIL::SigBit> multi_driver_bits;

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
                    {
                        auto existing =
                            driver_map.find(bit);

                        if (existing != driver_map.end() &&
                            existing->second != driver_cell)
                        {
                            multi_driver_bits.insert(bit);

                                                    }

                        // 保留原行为：
                        // 后遇到的 driver 仍覆盖 driver_map。
                        driver_map[bit] =
                            driver_cell;
                    }
                }
            }
            /*
 * ==================================================
 * Pattern D 使用：
 *
 * signal bit -> consumer cells
 *
 * 与 driver_map 相反，用于从 comparator 输出向后
 * 跟踪它是否只在 guard 条件下产生可观察影响。
 * ==================================================
 */
dict<RTLIL::SigBit, std::vector<RTLIL::Cell *>> user_map;

for (auto user_cell : module->cells())
{
    for (auto &conn : user_cell->connections())
    {
        if (!user_cell->input(conn.first))
            continue;

        RTLIL::SigSpec input =
            sigmap(conn.second);

        for (auto bit : input)
            user_map[bit].push_back(user_cell);
    }
}
/*
 * ==================================================
 * Pattern D 安全保护：
 *
 * 记录所有直接可观察的 module output bit。
 *
 * 如果 comparator 输出本身、或者 PMUX 输出直接
 * 接到模块输出，则不能依赖内部 DFFE guard 来缩窄。
 * ==================================================
 */
pool<RTLIL::SigBit> module_output_bits;

for (auto wire : module->wires())
{
    if (!wire->port_output)
        continue;

    RTLIL::SigSpec output =
        sigmap(RTLIL::SigSpec(wire));

    for (auto bit : output)
        module_output_bits.insert(bit);
}
/*
 * ==================================================
 * Pattern D:
 *
 * Guard-aware comparator narrowing
 *
 * 第一阶段只检测，不修改网表。
 *
 * 当前只识别：
 *
 *     control[k] == 1
 *
 * 作为正向 guard。
 *
 * 一个 $eq comparator 只有在它的所有有效用途都受到
 * 同一 control[k] guard 保护时，才作为候选。
 * ==================================================
 */

auto sig_contains_bit =
    [&](RTLIL::SigSpec signal,
        RTLIL::SigBit wanted)
    -> bool
{
    signal = sigmap(signal);
    wanted = sigmap(wanted);

    for (auto bit : signal)
        if (bit == wanted)
            return true;

    return false;
};


auto positive_guard_in_signal =
    [&](RTLIL::SigSpec signal,
        RTLIL::SigBit guard_bit)
    -> bool
{
    signal = sigmap(signal);
    guard_bit = sigmap(guard_bit);

    /*
     * guard 直接就是 EN。
     */
    if (signal.size() == 1 &&
        signal.as_bit() == guard_bit)
        return true;

    if (signal.size() != 1)
        return false;

    auto it =
        driver_map.find(
            signal.as_bit());

    if (it == driver_map.end())
        return false;

    RTLIL::Cell *driver =
        it->second;

    /*
     * $reduce_and(... guard_bit ...)
     */
    if (driver->type == ID($reduce_and))
    {
        RTLIL::SigSpec input =
            driver->getPort(ID::A);

        return sig_contains_bit(
            input,
            guard_bit);
    }

    /*
     * $and 的任意一侧出现 guard_bit。
     */
    if (driver->type == ID($and))
{
    return
        sig_contains_bit(
            driver->getPort(ID::A),
            guard_bit) ||
        sig_contains_bit(
            driver->getPort(ID::B),
            guard_bit);
}

/*
 * Verilog:
 *
 *     a && guard
 *
 * 常被 Yosys 保留为 $logic_and。
 *
 * v1 只接受两个输入都是 1 bit 的情况，
 * 避免多位 logic truth-value 带来的歧义。
 */
if (driver->type == ID($logic_and))
{
    RTLIL::SigSpec logic_a =
        sigmap(
            driver->getPort(ID::A));

    RTLIL::SigSpec logic_b =
        sigmap(
            driver->getPort(ID::B));

    if (logic_a.size() != 1 ||
        logic_b.size() != 1)
        return false;

    return
        logic_a.as_bit() == guard_bit ||
        logic_b.as_bit() == guard_bit;
}

return false;
};


std::function<bool(
    RTLIL::SigBit,
    RTLIL::SigBit,
    int)> guarded_use;


/*
 * 检查一个 PMUX 的输出是否只进入：
 *
 *     guard 控制的 $dffe.D
 *
 * 第一版故意严格。
 */
auto guarded_pmux_output =
    [&](RTLIL::Cell *pmux,
        RTLIL::SigBit guard_bit)
    -> bool
{
    RTLIL::SigSpec output =
        sigmap(
            pmux->getPort(ID::Y));

    bool found_user = false;

    pool<RTLIL::Cell *> checked_cells;

    for (auto out_bit : output)
    {        /*
         * PMUX 输出直接可观察时不能做这种优化。
         */
        if (module_output_bits.count(out_bit))
            return false;
        auto uit =
            user_map.find(out_bit);

        if (uit == user_map.end())
            continue;

        for (auto user : uit->second)
        {
            if (checked_cells.count(user))
                continue;

            checked_cells.insert(user);
            found_user = true;

            if (user->type != ID($dffe))
                return false;

            RTLIL::SigSpec d =
                sigmap(
                    user->getPort(ID::D));

            bool uses_pmux_data = false;

            for (auto bit : output)
            {
                if (sig_contains_bit(
                        d,
                        bit))
                {
                    uses_pmux_data = true;
                    break;
                }
            }

            if (!uses_pmux_data)
                return false;

            RTLIL::Const en_polarity =
                user->getParam(
                    ID::EN_POLARITY);

            /*
             * 第一版只支持正使能。
             */
            if (!en_polarity.as_bool())
                return false;

            RTLIL::SigSpec enable =
                user->getPort(ID::EN);

            if (!positive_guard_in_signal(
                    enable,
                    guard_bit))
                return false;
        }
    }

    return found_user;
};


/*
 * 从 comparator 输出向后检查。
 *
 * 允许穿过：
 *
 *     $reduce_bool
 *     $reduce_or
 *     $not
 *
 * 最终必须：
 *
 *   1. 进入包含 guard_bit 的 $reduce_and；
 *      或
 *   2. 作为 PMUX selector，而 PMUX 输出只写入
 *      guard 保护的 $dffe。
 */
guarded_use =
    [&](RTLIL::SigBit signal,
        RTLIL::SigBit guard_bit,
        int depth)
    -> bool
{
    if (depth > 6)
        return false;

    signal =
        sigmap(signal);

    auto it =
        user_map.find(signal);

    if (it == user_map.end() ||
        it->second.empty())
        return false;

    pool<RTLIL::Cell *> checked_users;

    for (auto user : it->second)
    {
        if (checked_users.count(user))
            continue;

        checked_users.insert(user);

        /*
         * 到达正向 guard AND。
         *
         * 一旦 comparator 结果和 guard_bit 在这里
         * 做 AND，后续逻辑已经被 guard 保护。
         */
        if (user->type == ID($reduce_and))
        {
            RTLIL::SigSpec input =
                user->getPort(ID::A);

            if (!sig_contains_bit(
                    input,
                    guard_bit))
                return false;

            continue;
        }


        /*
         * 普通 AND。
         */
        if (user->type == ID($and))
        {
            bool contains_guard =
                sig_contains_bit(
                    user->getPort(ID::A),
                    guard_bit) ||
                sig_contains_bit(
                    user->getPort(ID::B),
                    guard_bit);

            if (!contains_guard)
                return false;

            continue;
        }


        /*
         * 允许经过简单控制逻辑。
         */
        if (user->type == ID($reduce_bool) ||
            user->type == ID($reduce_or) ||
            user->type == ID($not))
        {
            RTLIL::SigSpec out =
                sigmap(
                    user->getPort(ID::Y));

            if (out.size() != 1)
                return false;

            if (!guarded_use(
                    out.as_bit(),
                    guard_bit,
                    depth + 1))
                return false;

            continue;
        }


        /*
         * comparator 用作 PMUX selector。
         */
        if (user->type == ID($pmux))
        {
            RTLIL::SigSpec selectors =
                sigmap(
                    user->getPort(ID::S));

            if (!sig_contains_bit(
                    selectors,
                    signal))
                return false;

            /*
             * 如果同时被 A/B 当数据使用，
             * 第一版直接拒绝。
             */
            if (sig_contains_bit(
                    user->getPort(ID::A),
                    signal) ||
                sig_contains_bit(
                    user->getPort(ID::B),
                    signal))
                return false;

            if (!guarded_pmux_output(
                    user,
                    guard_bit))
                return false;

            continue;
        }


        /*
         * 未知用途一律拒绝。
         */
        return false;
    }

    return true;
};


int pattern_d_candidates = 0;

for (auto eq_cell : module->cells())
{
    if (eq_cell->type != ID($eq))
        continue;

    RTLIL::SigSpec eq_a =
        sigmap(
            eq_cell->getPort(ID::A));

    RTLIL::SigSpec eq_b =
        sigmap(
            eq_cell->getPort(ID::B));

    RTLIL::SigSpec control;
RTLIL::Const constant;

/*
 * constant_on_b == true:
 *
 *     A = signal
 *     B = constant
 *
 * false:
 *
 *     A = constant
 *     B = signal
 */
bool constant_on_b = false;

    if (!eq_a.is_fully_const() &&
    eq_b.is_fully_const())
{
    control = eq_a;
    constant = eq_b.as_const();
    constant_on_b = true;
}
else if (
    eq_a.is_fully_const() &&
    !eq_b.is_fully_const())
{
    control = eq_b;
    constant = eq_a.as_const();
    constant_on_b = false;
}
    else
    {
        continue;
    }

    if (control.size() < 2 ||
        constant.size() != control.size())
        continue;
        /*
 * Pattern D v1 只处理最容易证明安全的形式：
 *
 *     unsigned N-bit == unsigned N-bit constant
 *
 * 暂时拒绝 signed / unequal-width comparator。
 */
int a_width =
    eq_cell->getParam(
        ID::A_WIDTH).as_int();

int b_width =
    eq_cell->getParam(
        ID::B_WIDTH).as_int();

bool a_signed =
    eq_cell->getParam(
        ID::A_SIGNED).as_bool();

bool b_signed =
    eq_cell->getParam(
        ID::B_SIGNED).as_bool();

if (a_signed ||
    b_signed ||
    a_width != b_width ||
    a_width != control.size())
    continue;

    RTLIL::SigSpec eq_y =
    sigmap(
        eq_cell->getPort(ID::Y));

if (eq_y.size() != 1)
    continue;

/*
 * comparator 自己直接连到模块输出：
 * 不能缩窄。
 */
if (module_output_bits.count(
        eq_y.as_bit()))
    continue;

    for (int bit = 0;
         bit < control.size();
         bit++)
    {
        /*
         * 第一版只考虑：
         *
         *     control[bit] == 1
         */
        if (constant[bit] != RTLIL::State::S1)
            continue;

        RTLIL::SigBit guard_bit =
            sigmap(control[bit]);

        if (!guarded_use(
                eq_y.as_bit(),
                guard_bit,
                0))
            continue;

        pattern_d_candidates++;

int old_width =
    control.size();

RTLIL::SigSpec narrowed_control;
RTLIL::Const narrowed_constant;

/*
 * RTLIL SigSpec/Const 的 bit 顺序都是：
 *
 * bit 0, bit 1, ...
 *
 * 所以逐位复制，跳过 guard bit 即可。
 */
for (int keep = 0;
     keep < old_width;
     keep++)
{
    if (keep == bit)
        continue;

    narrowed_control.append(
        control.extract(
            keep,
            1));

    narrowed_constant.append(
        RTLIL::Const(
            constant[keep],
            1));
}

if (narrowed_control.size() !=
        old_width - 1 ||
    narrowed_constant.size() !=
        old_width - 1)
{
    log_error(
        "Pattern D internal width mismatch.\n");
}

/*
 * 保持原来的 constant/signal 左右位置。
 */
if (constant_on_b)
{
    eq_cell->setPort(
        ID::A,
        narrowed_control);

    eq_cell->setPort(
        ID::B,
        narrowed_constant);
}
else
{
    eq_cell->setPort(
        ID::A,
        narrowed_constant);

    eq_cell->setPort(
        ID::B,
        narrowed_control);
}

eq_cell->setParam(
    ID::A_WIDTH,
    old_width - 1);

eq_cell->setParam(
    ID::B_WIDTH,
    old_width - 1);

log("\n");
log("GUARD-AWARE EQ REWRITE\n");
log("  eq          : %s\n",
    log_id(eq_cell));
log("  old width   : %d\n",
    old_width);
log("  guard bit   : %d\n",
    bit);
log("  guard value : 1\n");
log("  new width   : %d\n",
    old_width - 1);

break;
    }
}

if (pattern_d_candidates > 0)
{
    log("\n");
    log(
        "Pattern D candidates in module %s: %d\n",
        log_id(module),
        pattern_d_candidates);
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
                 * Pattern B:
                 * selector-conditioned branch constant folding
                 *
                 * S[i] = (control == CONST) 时，
                 * branch B[i] 中直接引用的 control bit
                 * 可以替换为对应常量。
                 * ----------------------------------------------
                 */
                if (info.selector_bank_valid)
                {
                    RTLIL::SigSpec new_port_b;
                    int replaced_bits = 0;

                    for (int branch = 0;
                         branch < info.s_width;
                         branch++)
                    {
                        RTLIL::SigSpec raw_branch =
                            info.port_b.extract(
                                branch * info.width,
                                info.width);

                        RTLIL::SigSpec mapped_branch =
                            sigmap(raw_branch);

                        const auto &cond =
                            info.conditions[branch];

                        for (int data_bit = 0;
                             data_bit < info.width;
                             data_bit++)
                        {
                            bool replaced = false;

                            for (int ctrl_bit = 0;
                                 ctrl_bit < info.ctrl_width;
                                 ctrl_bit++)
                            {
                                if (mapped_branch[data_bit] !=
                                    info.control[ctrl_bit])
                                    continue;

                                RTLIL::State value =
                                    cond.value[ctrl_bit];

                                if (value != RTLIL::State::S0 &&
                                    value != RTLIL::State::S1)
                                    continue;

                                new_port_b.append(
                                    RTLIL::SigSpec(
                                        RTLIL::Const(
                                            value,
                                            1)));

                                replaced = true;
                                replaced_bits++;
                                break;
                            }

                            if (!replaced)
                            {
                                new_port_b.append(
                                    raw_branch.extract(
                                        data_bit,
                                        1));
                            }
                        }
                    }

                    if (replaced_bits > 0)
                    {
                        info.cell->setPort(
                            ID::B,
                            new_port_b);

                        info.port_b =
                            new_port_b;

                        log("\n");
                        log("BRANCH-CONST FOLD\n");
                        log("  cell          : %s\n",
                            log_id(info.cell));
                        log("  replaced bits : %d\n",
                            replaced_bits);
                    }
                }


                /*
                 * ----------------------------------------------
                 * Pattern C:
                 * selector-conditioned expression
                 * constant folding
                 *
                 * S[i] = (control == CONST) 时，
                 * 在该 branch 中临时令：
                 *
                 *     control = CONST
                 *
                 * 然后使用 ConstEval 对 branch 数据锥
                 * 做按需常量传播。
                 *
                 * 能确定为 0/1 的 bit 替换为常量；
                 * 仍为 X 的 bit 保持原信号。
                 *
                 * Pattern B 已先处理直接 control bit，
                 * 因此这里主要覆盖：
                 *
                 *   $not
                 *   $xor
                 *   $and
                 *   $or
                 *   $reduce_*
                 *   以及其他 ConstEval 可安全求值的
                 *   组合表达式。
                 * ----------------------------------------------
                 */
                if (info.selector_bank_valid)
                {
                    RTLIL::SigSpec new_port_b;
                    int replaced_expr_bits = 0;

                    for (int branch = 0;
                         branch < info.s_width;
                         branch++)
                    {
                        RTLIL::SigSpec raw_branch =
                            info.port_b.extract(
                                branch * info.width,
                                info.width);

                        const auto &cond =
                            info.conditions[branch];

                        /*
                         * 每个 branch 都有自己独立的
                         * control == CONST 条件。
                         */
                        branch_consteval.clear();

                        branch_consteval.set(
                            info.control,
                            cond.value);

                        RTLIL::SigSpec evaluated_branch =
                            raw_branch;

                        RTLIL::SigSpec undef;

                        bool eval_ok =
                            branch_consteval.eval(
                                evaluated_branch,
                                undef);

                        /*
                         * eval 失败时完全保持原 branch。
                         *
                         * eval 成功后不要求整个 branch
                         * 都是常量：
                         *
                         *   0 / 1 -> 替换
                         *   X / Z -> 保留原信号
                         *
                         * 这样可以处理：
                         *
                         *   { external_data,
                         *     expression(control),
                         *     external_data,
                         *     expression(control) }
                         *
                         * 这种部分可折叠的 branch。
                         */
                        if (!eval_ok)
                        {
                            new_port_b.append(
                                raw_branch);
                            continue;
                        }

                        RTLIL::SigSpec mapped_branch =
                            sigmap(raw_branch);

                        for (int data_bit = 0;
                             data_bit < info.width;
                             data_bit++)
                        {
                            RTLIL::State value =
                                evaluated_branch[data_bit].data;

                            bool definite =
                                value == RTLIL::State::S0 ||
                                value == RTLIL::State::S1;

                            bool already_same_const =
                                false;

                            RTLIL::SigSpec mapped_bit =
                                mapped_branch.extract(
                                    data_bit,
                                    1);

                            /*
                             * 原本已经是同一个常量，
                             * 不计为 Pattern C 的收益。
                             */
                            if (definite &&
                                mapped_bit.is_fully_const())
                            {
                                RTLIL::Const original =
                                    mapped_bit.as_const();

                                if (original.size() == 1 &&
                                    original[0] == value)
                                {
                                    already_same_const =
                                        true;
                                }
                            }

                            if (definite &&
                                !already_same_const)
                            {
                                new_port_b.append(
                                    RTLIL::SigSpec(
                                        RTLIL::Const(
                                            value,
                                            1)));

                                replaced_expr_bits++;
                            }
                            else
                            {
                                new_port_b.append(
                                    raw_branch.extract(
                                        data_bit,
                                        1));
                            }
                        }
                    }

                    if (replaced_expr_bits > 0)
                    {
                        info.cell->setPort(
                            ID::B,
                            new_port_b);

                        info.port_b =
                            new_port_b;

                        log("\n");
                        log("BRANCH-EXPR CONST FOLD\n");
                        log("  cell          : %s\n",
                            log_id(info.cell));
                        log("  replaced bits : %d\n",
                            replaced_expr_bits);
                    }
                }


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

                /*
                 * H2 safety:
                 * 每个原 PMUX selector bit 必须只有唯一 cell driver。
                 *
                 * 这里只限制 H2，不改变现有 Pattern A/B/C/D。
                 */
                bool h2_selector_drivers_unique = true;

                for (int selector_index = 0;
                     selector_index < info.s_width;
                     selector_index++)
                {
                    RTLIL::SigSpec selector_bit =
                        sigmap(
                            info.port_s.extract(
                                selector_index,
                                1));

                    
                    if (selector_bit.size() != 1 ||
                        multi_driver_bits.count(
                            selector_bit.as_bit()))
                    {
                        h2_selector_drivers_unique = false;
                        break;
                    }
                }

                // H2：低两位控制轮换，
                // 其余控制位选择数据组。
                if (info.selector_bank_valid &&
                    info.full_decode &&
                    h2_selector_drivers_unique &&
                    info.ctrl_width >= 3 &&
                    info.ctrl_width <= 10 &&
                    info.width >= 4 &&
                    info.width % 4 == 0)
                {
                    const int lane_width = info.width / 4;
                    const int bank_count =
                        (1 << info.ctrl_width) / 4;

                    bool rotation_match = true;
                    bool meaningful_rotation = false;

                    for (int bank = 0;
                         bank < bank_count && rotation_match;
                         bank++)
                    {
                        const int base_branch =
                            info.branch_for_value[bank * 4];

                        RTLIL::SigSpec base_data = sigmap(
                            info.port_b.extract(
                                base_branch * info.width,
                                info.width));

                        // 第一版拒绝数据中的 X/Z 常量。
                        for (auto bit : base_data)
                        {
                            if (bit.wire == nullptr &&
                                bit.data != RTLIL::State::S0 &&
                                bit.data != RTLIL::State::S1)
                            {
                                rotation_match = false;
                                break;
                            }
                        }

                        for (int phase = 1;
                             phase < 4 && rotation_match;
                             phase++)
                        {
                            const int branch =
                                info.branch_for_value[
                                    bank * 4 + phase];

                            RTLIL::SigSpec actual = sigmap(
                                info.port_b.extract(
                                    branch * info.width,
                                    info.width));

                            RTLIL::SigSpec expected;

                            for (int lane = 0; lane < 4; lane++)
                            {
                                const int source_lane =
                                    (lane + phase) % 4;

                                expected.append(
                                    base_data.extract(
                                        source_lane * lane_width,
                                        lane_width));
                            }

                            if (actual != expected)
                            {
                                rotation_match = false;
                                break;
                            }

                            if (actual != base_data)
                                meaningful_rotation = true;
                        }
                    }

                    if (rotation_match && meaningful_rotation)
                    {
                        info.h2_rotation_candidate = true;
                        info.h2_lane_width = lane_width;
                        info.h2_bank_count = bank_count;

                        log("\nH2 ROTATION CANDIDATE (analysis only)\n");
                        log("  cell       : %s\n", log_id(info.cell));
                        log("  control    : %s\n",
                            log_signal(info.control));
                        log("  width      : %d\n", info.width);
                        log("  lane_width : %d\n", lane_width);
                        log("  banks      : %d\n", bank_count);
                        log("  coverage   : 100%%\n");
                        log("  exceptions : 0\n");
                        log("  gain       : not estimated\n");
                    }
                }
                pmux_infos.push_back(
                    info);
            }


            /*
             * ==================================================
             * H2 Stage 2
             *
             * 四 lane 循环换位重构：
             *
             * control[k-1:2] -> bank mux tree
             * control[0]     -> rotate 1 lane
             * control[1]     -> rotate 2 lanes
             *
             * detector 已保证：
             * - full decode
             * - 4 个等宽 lane
             * - 低两位为 phase
             * - 零 exception
             * ==================================================
             */
            std::vector<bool> h2_reserved(
                pmux_infos.size(),
                false);

            for (int h2_index = 0;
                 h2_index < int(pmux_infos.size());
                 h2_index++)
            {
                auto &info =
                    pmux_infos[h2_index];

                if (!info.h2_rotation_candidate)
                    continue;

                h2_reserved[h2_index] = true;

                const int width =
                    info.width;

                const int lane_width =
                    info.h2_lane_width;

                const int bank_count =
                    info.h2_bank_count;

                const int bank_ctrl_width =
                    info.ctrl_width - 2;

                if (lane_width <= 0 ||
                    lane_width * 4 != width ||
                    bank_ctrl_width <= 0 ||
                    bank_count !=
                        (1 << bank_ctrl_width))
                {
                    log_error(
                        "H2 internal parameter mismatch.\n");
                }

                RTLIL::IdString old_name =
                    info.cell->name;

                RTLIL::SigSpec old_y =
                    info.port_y;


                /*
                 * 创建 WIDTH-bit 2:1 mux。
                 */
                auto h2_make_mux =
                    [&](RTLIL::SigSpec in_a,
                        RTLIL::SigSpec in_b,
                        RTLIL::SigSpec select)
                    -> RTLIL::SigSpec
                {
                    if (in_a.size() != width ||
                        in_b.size() != width ||
                        select.size() != 1)
                    {
                        log_error(
                            "H2 mux width mismatch.\n");
                    }

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
                        RTLIL::SigSpec(wire));

                    return RTLIL::SigSpec(wire);
                };


                /*
                 * 四 lane 循环换位。
                 *
                 * RTLIL SigSpec 按低位到高位组织：
                 *
                 * shift=1:
                 * lane0 <- lane1
                 * lane1 <- lane2
                 * lane2 <- lane3
                 * lane3 <- lane0
                 */
                auto h2_rotate =
                    [&](RTLIL::SigSpec data,
                        int shift)
                    -> RTLIL::SigSpec
                {
                    RTLIL::SigSpec rotated;

                    for (int lane = 0;
                         lane < 4;
                         lane++)
                    {
                        int source_lane =
                            (lane + shift) % 4;

                        rotated.append(
                            data.extract(
                                source_lane *
                                    lane_width,
                                lane_width));
                    }

                    return rotated;
                };


                /*
                 * 每个 bank 只保留 phase=0：
                 *
                 * control value = bank * 4
                 */
                std::vector<RTLIL::SigSpec>
                    bank_level;

                for (int bank = 0;
                     bank < bank_count;
                     bank++)
                {
                    int branch =
                        info.branch_for_value[
                            bank * 4];

                    if (branch < 0 ||
                        branch >= info.s_width)
                    {
                        log_error(
                            "H2 invalid branch mapping.\n");
                    }

                    bank_level.push_back(
                        info.port_b.extract(
                            branch * width,
                            width));
                }


                /*
                 * 用 control[2], control[3], ...
                 * 构造二叉 mux tree。
                 *
                 * level 0:
                 *   bank0/1, bank2/3, ...
                 *
                 * level 1:
                 *   group0/1, ...
                 */
                for (int level = 0;
                     level < bank_ctrl_width;
                     level++)
                {
                    if (bank_level.size() < 2 ||
                        (bank_level.size() & 1))
                    {
                        log_error(
                            "H2 bank mux tree mismatch.\n");
                    }

                    std::vector<RTLIL::SigSpec>
                        next_level;

                    RTLIL::SigSpec select =
                        info.control.extract(
                            2 + level,
                            1);

                    for (int index = 0;
                         index <
                             int(bank_level.size());
                         index += 2)
                    {
                        next_level.push_back(
                            h2_make_mux(
                                bank_level[index],
                                bank_level[index + 1],
                                select));
                    }

                    bank_level.swap(
                        next_level);
                }

                if (bank_level.size() != 1)
                {
                    log_error(
                        "H2 final bank selection mismatch.\n");
                }

                RTLIL::SigSpec bank_data =
                    bank_level[0];


                /*
                 * phase bit 0:
                 *
                 * 0 -> rotate 0
                 * 1 -> rotate 1
                 */
                RTLIL::SigSpec stage1 =
                    h2_make_mux(
                        bank_data,
                        h2_rotate(
                            bank_data,
                            1),
                        info.control.extract(
                            0,
                            1));


                /*
                 * phase bit 1:
                 *
                 * 0 -> 保持
                 * 1 -> 再 rotate 2
                 *
                 * phase:
                 * 00 -> 0
                 * 01 -> 1
                 * 10 -> 2
                 * 11 -> 3
                 */
                RTLIL::SigSpec final_data =
                    h2_make_mux(
                        stage1,
                        h2_rotate(
                            stage1,
                            2),
                        info.control.extract(
                            1,
                            1));


                /*
                 * 删除原大 PMUX，
                 * 新结构接回原输出。
                 */
                module->remove(
                    info.cell);

                info.cell = nullptr;

                module->connect(
                    old_y,
                    final_data);


                log("\n");
                log("H2 ROTATION REBUILT\n");

                log(
                    "  old cell    : %s\n",
                    log_id(old_name));

                log(
                    "  width       : %d\n",
                    width);

                log(
                    "  lane_width  : %d\n",
                    lane_width);

                log(
                    "  banks       : %d\n",
                    bank_count);

                log(
                    "  bank_ctrl   : %d bits\n",
                    bank_ctrl_width);

                log(
                    "  phase       : control[1:0]\n");
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
                if (grouped[i] ||
                    h2_reserved[i])
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
                    if (grouped[j] ||
                        h2_reserved[j])
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

                            /*
 * Pattern A profitability gate
 *
 * 无特殊 pair：
 *     保留原 pair-swap 优化。
 *
 * 有 1 个特殊 pair：
 *     pair_count >= 8 时允许优化；
 *     pair_count == 4 且 WIDTH <= 2 时允许优化；
 *     其他情况跳过，避免面积反而增大。
 */
bool special_case_profitable =
    special_base_values.empty() ||
    (special_base_values.size() == 1 &&
     (pair_count >= 8 ||
      (pair_count == 4 &&
       info_a.width <= 2))) ||
    (special_base_values.size() == 2 &&
     pair_count >= 8);

bool profitable_pattern =
    swapped_pairs >= 2 &&
    swapped_pairs * 4 >=
        pair_count * 3 &&
    special_base_values.size() <= 2 &&
    special_case_profitable;

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

        /*
         * ==================================================
         * H3 Stage 1
         *
         * Priority $mux chain candidate detection.
         *
         * 识别候选结构；通过安全检查后由 Stage 2 重写 selector。
         *
         * 目标结构：
         *
         *   CONST_BASE
         *       |
         *   mux(lowest)
         *       |
         *      ...
         *       |
         *   mux(highest)
         *       |
         *      OUT
         *
         * 要求：
         *   - 连续 $mux
         *   - WIDTH 相同
         *   - S 均为 1 bit
         *   - child.Y == parent.A
         *   - 最低层 A 为常量
         *   - selector 不重复
         *   - depth >= 3
         * ==================================================
         */
        {
            SigMap h3_sigmap(module);

            std::vector<RTLIL::Cell *> h3_muxes;

            for (auto cell : module->cells())
            {
                if (cell->type != ID($mux))
                    continue;

                int width =
                    cell->getParam(ID::WIDTH).as_int();

                RTLIL::SigSpec a =
                    h3_sigmap(cell->getPort(ID::A));

                RTLIL::SigSpec b =
                    h3_sigmap(cell->getPort(ID::B));

                RTLIL::SigSpec sel =
                    h3_sigmap(cell->getPort(ID::S));

                RTLIL::SigSpec y =
                    h3_sigmap(cell->getPort(ID::Y));

                if (width <= 0)
                    continue;

                if (GetSize(a) != width ||
                    GetSize(b) != width ||
                    GetSize(y) != width ||
                    GetSize(sel) != 1)
                    continue;

                h3_muxes.push_back(cell);
            }


            /*
             * 当前 mux 的 Y 如果接到另一个 mux 的 A，
             * 那它就不是整条链最靠近输出的一层。
             */
            auto h3_has_parent =
                [&](RTLIL::Cell *cell) -> bool
            {
                int width =
                    cell->getParam(ID::WIDTH).as_int();

                RTLIL::SigSpec y =
                    h3_sigmap(
                        cell->getPort(ID::Y));

                for (auto other : h3_muxes)
                {
                    if (other == cell)
                        continue;

                    if (other->getParam(
                            ID::WIDTH).as_int() != width)
                        continue;

                    RTLIL::SigSpec other_a =
                        h3_sigmap(
                            other->getPort(ID::A));

                    if (other_a == y)
                        return true;
                }

                return false;
            };


            /*
             * 查找某个 A 是否来自另一个同宽 mux 的 Y。
             */
            auto h3_find_child =
                [&](const RTLIL::SigSpec &a,
                    int width,
                    bool &ambiguous)
                    -> RTLIL::Cell *
            {
                RTLIL::Cell *found = nullptr;
                ambiguous = false;

                for (auto candidate : h3_muxes)
                {
                    if (candidate->getParam(
                            ID::WIDTH).as_int() != width)
                        continue;

                    RTLIL::SigSpec candidate_y =
                        h3_sigmap(
                            candidate->getPort(ID::Y));

                    if (candidate_y != a)
                        continue;

                    if (found != nullptr)
                    {
                        ambiguous = true;
                        return nullptr;
                    }

                    found = candidate;
                }

                return found;
            };



            /*
             * 判断两个 canonical SigSpec 是否有任意 bit 重叠。
             */
            auto h3_sig_overlap =
                [&](const RTLIL::SigSpec &lhs,
                    const RTLIL::SigSpec &rhs)
                    -> bool
            {
                for (auto lhs_bit : lhs)
                    for (auto rhs_bit : rhs)
                        if (lhs_bit == rhs_bit)
                            return true;

                return false;
            };


            /*
             * 中间 mux 的 Y 必须是私有链路：
             *
             * child.Y 只能被 parent.A 使用。
             *
             * 如果还被其他 cell 输入或 module output 使用，
             * rewrite 会改变可观察的中间值，因此拒绝优化。
             */
            auto h3_intermediate_is_private =
                [&](RTLIL::Cell *child,
                    RTLIL::Cell *parent)
                    -> bool
            {
                RTLIL::SigSpec y =
                    h3_sigmap(
                        child->getPort(ID::Y));

                bool saw_expected_parent = false;

                for (auto user_cell : module->cells())
                {
                    for (auto &conn :
                         user_cell->connections())
                    {
                        if (!user_cell->input(
                                conn.first))
                            continue;

                        RTLIL::SigSpec input =
                            h3_sigmap(
                                conn.second);

                        if (!h3_sig_overlap(
                                input,
                                y))
                            continue;

                        /*
                         * 唯一允许的使用：
                         *
                         * child.Y -> parent.A
                         */
                        if (user_cell == parent &&
                            conn.first == ID::A &&
                            input == y &&
                            !saw_expected_parent)
                        {
                            saw_expected_parent = true;
                            continue;
                        }

                        return false;
                    }
                }

                if (!saw_expected_parent)
                    return false;


                /*
                 * 中间节点也不能直接成为 module output。
                 */
                for (auto wire : module->wires())
                {
                    if (!wire->port_output)
                        continue;

                    RTLIL::SigSpec output =
                        h3_sigmap(
                            RTLIL::SigSpec(wire));

                    if (h3_sig_overlap(
                            output,
                            y))
                        return false;
                }

                return true;
            };


            /*
             * 创建 1-bit $not。
             */
            auto h3_make_not =
                [&](RTLIL::SigSpec input)
                    -> RTLIL::SigSpec
            {
                RTLIL::Wire *wire =
                    module->addWire(
                        NEW_ID,
                        1);

                RTLIL::Cell *cell =
                    module->addCell(
                        NEW_ID,
                        ID($not));

                cell->setParam(
                    ID::A_SIGNED,
                    0);

                cell->setParam(
                    ID::A_WIDTH,
                    1);

                cell->setParam(
                    ID::Y_WIDTH,
                    1);

                cell->setPort(
                    ID::A,
                    input);

                cell->setPort(
                    ID::Y,
                    RTLIL::SigSpec(wire));

                return RTLIL::SigSpec(wire);
            };


            /*
             * 创建 1-bit $and。
             */
            auto h3_make_and =
                [&](RTLIL::SigSpec lhs,
                    RTLIL::SigSpec rhs)
                    -> RTLIL::SigSpec
            {
                RTLIL::Wire *wire =
                    module->addWire(
                        NEW_ID,
                        1);

                RTLIL::Cell *cell =
                    module->addCell(
                        NEW_ID,
                        ID($and));

                cell->setParam(
                    ID::A_SIGNED,
                    0);

                cell->setParam(
                    ID::B_SIGNED,
                    0);

                cell->setParam(
                    ID::A_WIDTH,
                    1);

                cell->setParam(
                    ID::B_WIDTH,
                    1);

                cell->setParam(
                    ID::Y_WIDTH,
                    1);

                cell->setPort(
                    ID::A,
                    lhs);

                cell->setPort(
                    ID::B,
                    rhs);

                cell->setPort(
                    ID::Y,
                    RTLIL::SigSpec(wire));

                return RTLIL::SigSpec(wire);
            };


            for (auto start : h3_muxes)
            {
                /*
                 * 只从最高优先级、最靠近输出的一层开始，
                 * 防止同一条链重复报告。
                 */
                if (h3_has_parent(start))
                    continue;

                int width =
                    start->getParam(ID::WIDTH).as_int();

                std::vector<RTLIL::Cell *> chain;
                std::vector<RTLIL::SigBit> selectors;
                std::vector<RTLIL::Cell *> visited;

                bool valid = true;
                RTLIL::Cell *current = start;

                while (current != nullptr)
                {
                    bool repeated_cell = false;

                    for (auto old_cell : visited)
                        if (old_cell == current)
                            repeated_cell = true;

                    if (repeated_cell)
                    {
                        valid = false;
                        break;
                    }

                    visited.push_back(current);
                    chain.push_back(current);


                    RTLIL::SigSpec sel =
                        h3_sigmap(
                            current->getPort(ID::S));

                    if (GetSize(sel) != 1)
                    {
                        valid = false;
                        break;
                    }

                    bool repeated_selector = false;

                    for (auto old_sel : selectors)
                        if (old_sel == sel[0])
                            repeated_selector = true;

                    if (repeated_selector)
                    {
                        valid = false;
                        break;
                    }

                    selectors.push_back(sel[0]);


                    RTLIL::SigSpec a =
                        h3_sigmap(
                            current->getPort(ID::A));

                    bool ambiguous = false;

                    RTLIL::Cell *child =
                        h3_find_child(
                            a,
                            width,
                            ambiguous);

                    if (ambiguous)
                    {
                        valid = false;
                        break;
                    }

                    /*
                     * 找不到下一层，说明到达链底。
                     */
                    if (child == nullptr)
                    {
                        if (!a.is_fully_const())
                            valid = false;

                        break;
                    }

                    current = child;
                }


                if (!valid)
                    continue;

                if (chain.size() < 3)
                    continue;


                log("\n");
                total_h3_candidates++;

                log(
                    "H3 PRIORITY MUX CHAIN CANDIDATE\n");

                log(
                    "  width       : %d\n",
                    width);

                log(
                    "  depth       : %zu\n",
                    chain.size());

                log(
                    "  priority    : high -> low\n");

                for (size_t k = 0;
                     k < chain.size();
                     k++)
                {
                    log(
                        "    [%zu] %s\n",
                        k,
                        log_id(chain[k]));
                }


                /*
                 * ==================================================
                 * H3 Stage 2
                 *
                 * Safety check:
                 * 所有中间 Y 都必须只服务于上一层 A。
                 * ==================================================
                 */
                bool private_chain = true;

                for (size_t k = 1;
                     k < chain.size();
                     k++)
                {
                    if (!h3_intermediate_is_private(
                            chain[k],
                            chain[k - 1]))
                    {
                        private_chain = false;
                        break;
                    }
                }

                if (!private_chain)
                {
                    log(
                        "H3 PRIORITY MUX CHAIN SKIPPED"
                        " (shared intermediate Y)\n");

                    continue;
                }


                /*
                 * 保存原 selector。
                 *
                 * chain 顺序：
                 *
                 *   [0] highest priority
                 *   [1] next
                 *   ...
                 *   [N-1] lowest priority
                 */
                std::vector<RTLIL::SigSpec>
                    original_selectors;

                for (auto mux : chain)
                {
                    original_selectors.push_back(
                        h3_sigmap(
                            mux->getPort(ID::S)));
                }


                /*
                 * highest selector 保持原样。
                 *
                 * effective[0] = s0
                 *
                 * 后续：
                 *
                 * effective[1] =
                 *     ~s0 & s1
                 *
                 * effective[2] =
                 *     ~s0 & ~s1 & s2
                 *
                 * ...
                 */
                RTLIL::SigSpec prefix =
                    h3_make_not(
                        original_selectors[0]);

                for (size_t k = 1;
                     k < chain.size();
                     k++)
                {
                    RTLIL::SigSpec effective =
                        h3_make_and(
                            prefix,
                            original_selectors[k]);

                    /*
                     * 只修改 S。
                     *
                     * A / B / Y 完全保持不动。
                     */
                    chain[k]->setPort(
                        ID::S,
                        effective);


                    /*
                     * 最后一层后面不再需要 prefix。
                     */
                    if (k + 1 < chain.size())
                    {
                        RTLIL::SigSpec not_sel =
                            h3_make_not(
                                original_selectors[k]);

                        prefix =
                            h3_make_and(
                                prefix,
                                not_sel);
                    }
                }


                total_h3_rebuilt++;

                log(
                    "H3 PRIORITY MUX CHAIN REBUILT\n");

                log(
                    "  width       : %d\n",
                    width);

                log(
                    "  depth       : %zu\n",
                    chain.size());

                log(
                    "  transform   : priority -> mutually-exclusive selectors\n");
            }
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

            log(
                "Total H3 candidates: %d\n",
                total_h3_candidates);

            log(
                "Total H3 rebuilt: %d\n",
                total_h3_rebuilt);
    }
} PmuxOptPass;


PRIVATE_NAMESPACE_END