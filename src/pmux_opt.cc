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

struct PmuxOptPass : public Pass
{
    PmuxOptPass()
        : Pass("pmux_opt", "inspect and optimize $pmux cells")
    {
    }

    void help() override
    {
        log("\n");
        log("    pmux_opt [selection]\n");
        log("\n");
        log("Inspect $pmux cells in the current design.\n");
        log("Current version also detects repeated B input slices.\n");
        log("\n");
    }

    void execute(std::vector<std::string> args,
                 RTLIL::Design *design) override
    {
        log_header(design, "Executing PMUX_OPT pass.\n");

        extra_args(args, 1, design);

        int pmux_count = 0;

        for (auto module : design->selected_modules())
        {
            // SigMap 用于把等价的连线规范到统一表示。
            SigMap sigmap(module);
dict<RTLIL::SigBit, RTLIL::Cell *> driver_map;

for (auto driver_cell : module->cells())
{
    for (auto &conn : driver_cell->connections())
    {
        if (!driver_cell->output(conn.first))
            continue;

        RTLIL::SigSpec output_sig =
            sigmap(conn.second);

        for (auto bit : output_sig)
            driver_map[bit] = driver_cell;
    }
}
            for (auto cell : module->selected_cells())
            {
                if (cell->type != ID($pmux))
                    continue;

                pmux_count++;

                int width =
                    cell->getParam(ID::WIDTH).as_int();

                int s_width =
                    cell->getParam(ID::S_WIDTH).as_int();

                RTLIL::SigSpec port_a =
                    cell->getPort(ID::A);

                RTLIL::SigSpec port_b =
                    cell->getPort(ID::B);

                RTLIL::SigSpec port_s =
                    cell->getPort(ID::S);

                RTLIL::SigSpec port_y =
                    cell->getPort(ID::Y);

                log("\n");
                log("Found $pmux\n");
                log("  module   : %s\n",
                    log_id(module));
                log("  cell     : %s\n",
                    log_id(cell));
                log("  WIDTH    : %d\n",
                    width);
                log("  S_WIDTH  : %d\n",
                    s_width);

                log("  A        : %s\n",
                    log_signal(port_a));

                log("  Y        : %s\n",
                    log_signal(port_y));

                // 保存不同的 B 数据值。
                std::vector<RTLIL::SigSpec> group_values;

                // 保存每一种 B 数据值对应哪些 input。
                std::vector<std::vector<int>> group_indices;

                std::vector<SelectorCondition> selector_conditions(s_width);
                for (int i = 0; i < s_width; i++)
                {
                    RTLIL::SigSpec s_bit =
                        port_s.extract(i, 1);
                        RTLIL::SigSpec normalized_s =
    sigmap(s_bit);

RTLIL::Cell *driver = nullptr;

if (normalized_s.size() == 1)
{
    RTLIL::SigBit key =
        normalized_s.as_bit();

    auto it = driver_map.find(key);

    if (it != driver_map.end())
        driver = it->second;
}

                    RTLIL::SigSpec b_slice =
                        port_b.extract(i * width, width);

                    log("  input[%d]\n", i);
                    log("    S[%d]   : %s\n",
                        i,
                        log_signal(s_bit));
                        if (driver != nullptr)
{
    log("    driver : %s (%s)\n",
        log_id(driver),
        log_id(driver->type));

    if (driver->type == ID($eq))
    {
        RTLIL::SigSpec cond_a =
            sigmap(driver->getPort(ID::A));

        RTLIL::SigSpec cond_b =
            sigmap(driver->getPort(ID::B));

        log("    cond A : %s\n",
            log_signal(cond_a));

        log("    cond B : %s\n",
            log_signal(cond_b));
            if (!cond_a.is_fully_const() &&
    cond_b.is_fully_const())
{
    selector_conditions[i].valid = true;
    selector_conditions[i].signal = cond_a;
    selector_conditions[i].value =
        cond_b.as_const();
}
else if (cond_a.is_fully_const() &&
         !cond_b.is_fully_const())
{
    selector_conditions[i].valid = true;
    selector_conditions[i].signal = cond_b;
    selector_conditions[i].value =
        cond_a.as_const();
}
    }
    else if (driver->type == ID($logic_not))
    {
        RTLIL::SigSpec cond_a =
            sigmap(driver->getPort(ID::A));

        log("    cond A : %s\n",
            log_signal(cond_a));

        log("    cond B : zero\n");
        if (!cond_a.is_fully_const())
{
    selector_conditions[i].valid = true;
    selector_conditions[i].signal = cond_a;
    selector_conditions[i].value =
        RTLIL::Const(0, cond_a.size());
}
    }
}
else
{
    log("    driver : <not found>\n");
}

                    log("    B[%d:%d]: %s\n",
                        i * width + width - 1,
                        i * width,
                        log_signal(b_slice));

                    // 将信号规范化，便于比较两个 B 是否实际上相同。
                    RTLIL::SigSpec normalized_b =
                        sigmap(b_slice);

                    int group_id = -1;

                    // 查找之前是否已经出现过相同的 B。
                    for (int g = 0;
                         g < int(group_values.size());
                         g++)
                    {
                        if (group_values[g] == normalized_b)
                        {
                            group_id = g;
                            break;
                        }
                    }

                    // 第一次出现这种 B，就新建一组。
                    if (group_id == -1)
                    {
                        group_values.push_back(normalized_b);
                        group_indices.push_back(
                            std::vector<int>());

                        group_id =
                            int(group_values.size()) - 1;
                    }

                    group_indices[group_id].push_back(i);
                }

                log("  Duplicate B analysis:\n");

                int duplicate_groups = 0;

                for (int g = 0;
     g < int(group_values.size());
     g++)
{
    if (group_indices[g].size() < 2)
        continue;

    duplicate_groups++;

    log("    value %s appears in inputs:",
        log_signal(group_values[g]));

    for (int index : group_indices[g])
        log(" %d", index);

    log("\n");

    bool mutually_exclusive = true;
    bool first_condition = true;

    RTLIL::SigSpec common_signal;
    std::vector<RTLIL::Const> seen_values;

    for (int index : group_indices[g])
    {
        const auto &cond =
            selector_conditions[index];

        if (!cond.valid)
        {
            mutually_exclusive = false;
            break;
        }

        if (first_condition)
        {
            common_signal = cond.signal;
            first_condition = false;
        }
        else if (cond.signal != common_signal)
        {
            mutually_exclusive = false;
            break;
        }

        for (const auto &value : seen_values)
        {
            if (value == cond.value)
            {
                mutually_exclusive = false;
                break;
            }
        }

        if (!mutually_exclusive)
            break;

        seen_values.push_back(cond.value);
    }

    if (mutually_exclusive)
        log("    mutual exclusion: PROVED\n");
    else
        log("    mutual exclusion: NOT PROVED\n");
}

                if (duplicate_groups == 0)
                {
                    log("    No duplicate B groups.\n");
                }
            }
        }

        log("\n");
        log("Total $pmux cells: %d\n",
            pmux_count);
    }
} PmuxOptPass;

PRIVATE_NAMESPACE_END