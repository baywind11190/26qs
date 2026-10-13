// Test-only entry point: verify 6.1 without invoking older pass rules.
// The runner supplies the exact candidate source via its include directory.
#include "candidate.cc"

struct EnableFeedbackTestPass : public Yosys::Pass
{
    EnableFeedbackTestPass() : Pass("enable_feedback_test", "test 6.1 in isolation") {}
    void execute(std::vector<std::string> args, Yosys::RTLIL::Design *design) override
    {
        extra_args(args, 1, design);
        for (auto module : design->selected_modules()) {
            Yosys::SigMap sigmap(module);
            Yosys::dict<Yosys::SigBit, Yosys::RTLIL::Cell *> drivers;
            Yosys::pool<Yosys::SigBit> multiple;
            for (auto cell : module->cells()) for (auto &port : cell->connections()) {
                if (!cell->output(port.first)) continue;
                for (auto bit : sigmap(port.second)) {
                    if (drivers.count(bit) && drivers.at(bit) != cell) multiple.insert(bit);
                    drivers[bit] = cell;
                }
            }
            Yosys::log("Total enable-feedback rebuilt: %d\n",
                EnableFeedback(module, sigmap, drivers, multiple).run());
        }
    }
} EnableFeedbackTestPass;
