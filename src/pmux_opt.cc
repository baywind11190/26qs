#include "kernel/yosys.h"

USING_YOSYS_NAMESPACE
PRIVATE_NAMESPACE_BEGIN

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
        log("Current version prints PMUX ports and input slices.\n");
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

                for (int i = 0; i < s_width; i++)
                {
                    RTLIL::SigSpec s_bit =
                        port_s.extract(i, 1);

                    RTLIL::SigSpec b_slice =
                        port_b.extract(i * width, width);

                    log("  input[%d]\n", i);
                    log("    S[%d]   : %s\n",
                        i,
                        log_signal(s_bit));

                    log("    B[%d:%d]: %s\n",
                        i * width + width - 1,
                        i * width,
                        log_signal(b_slice));
                }
            }
        }

        log("\n");
        log("Total $pmux cells: %d\n",
            pmux_count);
    }
} PmuxOptPass;

PRIVATE_NAMESPACE_END
