
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
 *   3.2 同前缀比较器因式分解
 *
 * 4 分组轮换因式分解
 *   4.1 分组选择与四路循环轮换因式分解
 *
 * 5 优先级多路选择优化
 *   5.1 优先级多路选择链互斥选择因式分解
 *
 * 6 寄存器更新条件优化
 *   6.1 比较条件共享与寄存器使能反馈联合重构
 *
 * 7 已撤除：映射后局部LUT优化（2026-10-30 答疑 C147.1）
 *
 * 8 译码多路选择重构
 *   8.1 译码PMUX默认分支补全与二进制重构
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
#include "kernel/ffinit.h"
#include "kernel/celltypes.h"
#include <functional>
#include <set>
#include <array>
#include <cstdint>
#include <map>
#include <tuple>

USING_YOSYS_NAMESPACE
PRIVATE_NAMESPACE_BEGIN

// 8.1 Recover a binary address from an injective equality decoder. Missing
// addresses retain the original PMUX default; no reachability assumptions.
static int optimize_decoded_pmux(RTLIL::Design *design)
{
    std::unique_ptr<CellTypes> types;
    int rebuilt = 0;
    for (auto module : design->selected_modules()) {
        if (module->get_bool_attribute(ID::keep))
            continue;
        bool possible = false;
        for (auto cell : module->selected_cells())
            if (cell->type == ID($pmux) && !cell->get_bool_attribute(ID::keep) &&
                cell->hasParam(ID::S_WIDTH) && cell->getParam(ID::S_WIDTH).as_int() >= 2 &&
                cell->getParam(ID::S_WIDTH).as_int() <= 8) {
                possible = true;
                break;
            }
        if (!possible)
            continue;
        if (!types)
            types = std::make_unique<CellTypes>(design);
        SigMap sigmap(module);
        dict<RTLIL::SigBit, std::vector<RTLIL::Cell *>> drivers;
        pool<RTLIL::SigBit> pinned;
        for (auto wire : module->wires())
            if (wire->port_input || wire->get_bool_attribute(ID::keep) || wire->attributes.count(ID::init))
                for (auto bit : sigmap(wire))
                    pinned.insert(bit);
        for (auto cell : module->cells()) {
            bool known = types->cell_known(cell->type);
            for (auto &port : cell->connections()) {
                if (!known)
                    for (auto bit : sigmap(port.second))
                        pinned.insert(bit);
                if (known && types->cell_output(cell->type, port.first))
                    for (auto bit : sigmap(port.second))
                        drivers[bit].push_back(cell);
            }
        }
        pool<RTLIL::Cell *> removed;
        std::vector<RTLIL::Cell *> cells = module->selected_cells();
        for (auto cell : cells) {
            if (cell->type != ID($pmux) || cell->get_bool_attribute(ID::keep) ||
                !cell->hasParam(ID::WIDTH) || !cell->hasParam(ID::S_WIDTH) ||
                !cell->hasPort(ID::A) || !cell->hasPort(ID::B) ||
                !cell->hasPort(ID::S) || !cell->hasPort(ID::Y))
                continue;
            int width = cell->getParam(ID::WIDTH).as_int();
            int count = cell->getParam(ID::S_WIDTH).as_int();
            RTLIL::SigSpec a = sigmap(cell->getPort(ID::A)), b = sigmap(cell->getPort(ID::B));
            RTLIL::SigSpec s = sigmap(cell->getPort(ID::S)), y = sigmap(cell->getPort(ID::Y));
            if (width < 1 || count < 2 || count > 8 || GetSize(a) != width ||
                int64_t(GetSize(b)) != int64_t(width) * count || GetSize(s) != count || GetSize(y) != width)
                continue;
            bool valid = true;
            RTLIL::SigSpec control;
            dict<int, RTLIL::SigSpec> branches;
            for (int branch = 0; branch < count; branch++) {
                auto driver = drivers.find(s[branch]);
                if (pinned.count(s[branch]) || driver == drivers.end() || GetSize(driver->second) != 1) {
                    valid = false;
                    break;
                }
                RTLIL::Cell *decode = driver->second[0];
                if (removed.count(decode) || decode->get_bool_attribute(ID::keep) || !decode->hasPort(ID::A) ||
                    !decode->hasPort(ID::Y) || GetSize(decode->getPort(ID::Y)) != 1) {
                    valid = false;
                    break;
                }
                RTLIL::SigSpec signal;
                RTLIL::Const value;
                if (decode->type == ID($logic_not)) {
                    signal = sigmap(decode->getPort(ID::A));
                    value = RTLIL::Const(0, GetSize(signal));
                } else if (decode->type == ID($eq) && decode->hasPort(ID::B) &&
                           decode->hasParam(ID::A_SIGNED) && decode->hasParam(ID::B_SIGNED)) {
                    signal = sigmap(decode->getPort(ID::A));
                    RTLIL::SigSpec constant = sigmap(decode->getPort(ID::B));
                    if (signal.is_fully_const())
                        std::swap(signal, constant);
                    if (!constant.is_fully_const() || !constant.as_const().is_fully_def() ||
                        GetSize(signal) != GetSize(constant) || decode->getParam(ID::A_SIGNED).as_bool() ||
                        decode->getParam(ID::B_SIGNED).as_bool()) {
                        valid = false;
                        break;
                    }
                    value = constant.as_const();
                } else {
                    valid = false;
                    break;
                }
                // This bounded first implementation has at most eight addresses.
                if (GetSize(signal) < 2 || GetSize(signal) > 3) {
                    valid = false;
                    break;
                }
                pool<RTLIL::SigBit> distinct;
                for (auto bit : signal)
                    if (bit.wire == nullptr || !distinct.insert(bit).second ||
                        (drivers.count(bit) && GetSize(drivers.at(bit)) != 1))
                        valid = false;
                if (!valid)
                    break;
                if (GetSize(control) == 0)
                    control = signal;
                int address = value.as_int();
                if (signal != control || branches.count(address)) {
                    valid = false;
                    break;
                }
                branches[address] = b.extract(branch * width, width);
            }
            if (!valid || GetSize(control) == 0)
                continue;
            pool<RTLIL::SigBit> outputs;
            for (auto bit : y) {
                outputs.insert(bit);
                if (bit.wire == nullptr || pinned.count(bit) || GetSize(drivers[bit]) != 1)
                    valid = false;
            }
            std::vector<RTLIL::SigSpec> table;
            for (int address = 0; address < (1 << GetSize(control)); address++) {
                RTLIL::SigSpec data = branches.count(address) ? branches.at(address) : a;
                for (auto bit : data)
                    if ((bit.wire == nullptr && bit != State::S0 && bit != State::S1) || outputs.count(bit))
                        valid = false;
                table.push_back(data);
            }
            if (!valid)
                continue;
            // At most three decoder bits: compare the <=6 variable orders
            // using only shared one-bit mux nodes, then emit one selected tree.
            // No synthesis, LUT rewriting, or reachability assumptions here.
            std::vector<int> order, best_order;
            for (int bit = 0; bit < GetSize(control); bit++) order.push_back(bit);
            best_order = order;
            dict<RTLIL::SigBit, int> leaf_ids;
            for (auto &entry : table)
                for (auto bit : entry)
                    if (!leaf_ids.count(bit)) leaf_ids[bit] = GetSize(leaf_ids);
            int best_cost = -1;
            do {
                std::map<std::tuple<int, int, int>, int> nodes;
                std::function<int(int, int, int)> score = [&](int depth, int address, int output) -> int {
                    if (depth == GetSize(control)) return leaf_ids.at(table[address][output]);
                    int bit = order[depth];
                    int low = score(depth + 1, address, output);
                    int high = score(depth + 1, address | (1 << bit), output);
                    if (low == high) return low;
                    auto key = std::make_tuple(bit, low, high);
                    auto found = nodes.find(key);
                    if (found != nodes.end()) return found->second;
                    int id = GetSize(leaf_ids) + GetSize(nodes);
                    nodes.emplace(key, id);
                    return id;
                };
                for (int output = 0; output < width; output++) score(0, 0, output);
                if (best_cost < 0 || GetSize(nodes) < best_cost) {
                    best_cost = GetSize(nodes);
                    best_order = order;
                }
            } while (std::next_permutation(order.begin(), order.end()));
            std::function<RTLIL::SigSpec(int, int)> build = [&](int depth, int address) -> RTLIL::SigSpec {
                if (depth == GetSize(control)) return table[address];
                int bit = best_order[depth];
                RTLIL::SigSpec low = build(depth + 1, address);
                RTLIL::SigSpec high = build(depth + 1, address | (1 << bit));
                if (low == high) return low;
                RTLIL::SigSpec result = depth == 0 ? cell->getPort(ID::Y) :
                    RTLIL::SigSpec(module->addWire(NEW_ID, width));
                module->addMux(NEW_ID, low, high, control.extract(bit, 1), result);
                return result;
            };
            RTLIL::SigSpec result = build(0, 0);
            if (result != cell->getPort(ID::Y))
                module->connect(cell->getPort(ID::Y), result);
            log("8.1 DECODED PMUX REBUILT: width=%d control=%d explicit=%d\n",
                width, GetSize(control), GetSize(branches));
            removed.insert(cell);
            module->remove(cell);
            rebuilt++;
        }
    }
    return rebuilt;
}


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


// 6.1: bounded, structural three-condition enable/data feedback factoring.
// Original enables: G&(A|B), G&(A|C), G&!C. No signal names or
// particular command constants are used. Only the final one expands enable.
struct EnableFeedback
{
    RTLIL::Module *module;
    SigMap &sigmap;
    const dict<SigBit, RTLIL::Cell *> &drivers;
    const pool<SigBit> &multiple;
    FfInitVals init;
    std::unique_ptr<ConstEval> evaluator;
    struct Predicate { SigSpec control; std::vector<int> values; };
    struct Record { RTLIL::Cell *cell; Predicate pred; std::vector<SigBit> guard; bool complement; };

    EnableFeedback(RTLIL::Module *m, SigMap &s,
                   const dict<SigBit, RTLIL::Cell *> &d, const pool<SigBit> &p)
        : module(m), sigmap(s), drivers(d), multiple(p) { init.set(&sigmap, module); }

    RTLIL::Cell *driver(SigBit bit) const
    {
        bit = sigmap(bit);
        auto it = drivers.find(bit);
        if (!bit.wire || multiple.count(bit) || it == drivers.end()) return nullptr;
        auto c = it->second;
        if (c->get_bool_attribute(ID::keep) || !c->hasPort(ID::Y) ||
            sigmap(c->getPort(ID::Y)) != SigSpec(bit)) return nullptr;
        return c;
    }

    bool factors(SigBit bit, std::vector<SigBit> &out, int depth = 0)
    {
        if (depth > 6 || out.size() > 8) return false;
        bit = sigmap(bit);
        if (!bit.wire) return bit == State::S1;
        if (multiple.count(bit)) return false;
        auto c = driver(bit);
        if (c && c->type == ID($reduce_and)) {
            for (auto b : sigmap(c->getPort(ID::A)))
                if (!factors(b, out, depth+1)) return false;
        } else if (c && (c->type == ID($and) || c->type == ID($logic_and)) &&
                   GetSize(c->getPort(ID::A)) == 1 && GetSize(c->getPort(ID::B)) == 1) {
            if (!factors(c->getPort(ID::A)[0], out, depth+1) ||
                !factors(c->getPort(ID::B)[0], out, depth+1)) return false;
        } else out.push_back(bit);
        return out.size() <= 8;
    }

    bool predicate(SigBit bit, Predicate &p, int depth = 0)
    {
        if (depth > 6) return false;
        auto c = driver(bit);
        if (!c) return false;
        if (c->type == ID($eq)) {
            if (c->getParam(ID::A_SIGNED).as_bool() || c->getParam(ID::B_SIGNED).as_bool()) return false;
            auto a = sigmap(c->getPort(ID::A)), b = sigmap(c->getPort(ID::B));
            if (a.is_fully_const()) std::swap(a, b);
            if (GetSize(a) < 8 || GetSize(a) > 16 || GetSize(a) != GetSize(b) ||
                !b.is_fully_const() || !b.as_const().is_fully_def()) return false;
            pool<SigBit> seen;
            for (auto x : a) {
                if (!x.wire || multiple.count(x) || seen.count(x)) return false;
                seen.insert(x);
            }
            if (!p.control.empty() && p.control != a) return false;
            p.control = a;
            p.values.push_back(b.as_const().as_int());
        } else if (c->type == ID($reduce_or) || c->type == ID($reduce_bool)) {
            if (GetSize(c->getPort(ID::A)) > 3) return false;
            for (auto b : c->getPort(ID::A)) if (!predicate(b, p, depth+1)) return false;
        } else if ((c->type == ID($or) || c->type == ID($logic_or)) &&
                   GetSize(c->getPort(ID::A)) == 1 && GetSize(c->getPort(ID::B)) == 1) {
            if (!predicate(c->getPort(ID::A)[0], p, depth+1) ||
                !predicate(c->getPort(ID::B)[0], p, depth+1)) return false;
        } else return false;
        if (p.values.size() > 3) return false;
        std::sort(p.values.begin(), p.values.end());
        p.values.erase(std::unique(p.values.begin(), p.values.end()), p.values.end());
        return true;
    }

    bool record(RTLIL::Cell *c, Record &r)
    {
        if (c->type != ID($dffe) || !module->selected(c) || c->get_bool_attribute(ID::keep) ||
            !c->getParam(ID::EN_POLARITY).as_bool()) return false;
        int width = c->getParam(ID::WIDTH).as_int();
        if (width < 1 || width > 64 || GetSize(c->getPort(ID::D)) != width ||
            GetSize(c->getPort(ID::Q)) != width || GetSize(c->getPort(ID::CLK)) != 1 ||
            GetSize(c->getPort(ID::EN)) != 1) return false;
        for (auto b : sigmap(c->getPort(ID::Q)))
            if (!b.wire || multiple.count(b) || init(b) != State::Sx) return false;
        std::vector<SigBit> fs;
        if (!factors(c->getPort(ID::EN)[0], fs)) return false;
        bool found = false;
        for (auto bit : fs) {
            auto d = driver(bit);
            bool neg = d && (d->type == ID($not) || d->type == ID($logic_not)) && GetSize(d->getPort(ID::A)) == 1;
            Predicate p;
            if (predicate(neg ? d->getPort(ID::A)[0] : bit, p) &&
                p.values.size() == (neg ? 1u : 2u)) {
                if (found) return false;
                found = true; r.pred = p; r.complement = neg;
            } else r.guard.push_back(bit);
        }
        std::sort(r.guard.begin(), r.guard.end());
        r.guard.erase(std::unique(r.guard.begin(), r.guard.end()), r.guard.end());
        r.cell = c;
        return found && !r.guard.empty() && r.guard.size() <= 4 && (!r.complement || width == 1);
    }

    bool clean_cone(SigSpec data, SigSpec control)
    {
        pool<SigBit> visited, boundary;
        for (auto b : control) boundary.insert(b);
        std::vector<SigBit> todo;
        for (auto b : sigmap(data)) todo.push_back(b);
        while (!todo.empty()) {
            auto b = todo.back(); todo.pop_back();
            if (multiple.count(b)) return false;
            if (!b.wire || boundary.count(b) || visited.count(b)) continue;
            visited.insert(b);
            if (visited.size() > 256) return false;
            auto it = drivers.find(b);
            if (it == drivers.end()) continue;
            auto c = it->second;
            // Sequential outputs are unknown boundaries, never evaluated here.
            if (c->type == ID($dffe) || c->type == ID($dff)) continue;
            for (auto &port : c->connections()) if (c->input(port.first))
                for (auto input : sigmap(port.second)) todo.push_back(input);
        }
        return true;
    }

    SigSpec evaluate(SigSpec data, SigSpec control, int value)
    {
        // Preserve unresolved inputs as symbolic wires. In particular, X===X
        // must not turn an equality between two external inputs into constant 1.
        if (!evaluator) evaluator.reset(new ConstEval(module));
        evaluator->clear();
        evaluator->set(control, RTLIL::Const(value, GetSize(control)));
        if (!evaluator->eval(data)) return RTLIL::Const(State::Sx, GetSize(data));
        return data;
    }

    bool compatible(const Record &a, const Record &b)
    {
        return a.pred.control == b.pred.control && a.guard == b.guard &&
            sigmap(a.cell->getPort(ID::CLK)) == sigmap(b.cell->getPort(ID::CLK)) &&
            a.cell->getParam(ID::CLK_POLARITY) == b.cell->getParam(ID::CLK_POLARITY);
    }

    SigSpec invert(SigSpec a) { auto y = module->addWire(NEW_ID); module->addNot(NEW_ID, a, y); return y; }
    SigSpec reduce(SigSpec a) {
        if (a.empty()) return State::S1;
        if (GetSize(a) == 1) return a;
        auto y = module->addWire(NEW_ID); module->addReduceAnd(NEW_ID, a, y); return y;
    }
    SigSpec binary(SigSpec a, SigSpec b, int kind) {
        auto y = module->addWire(NEW_ID);
        if (kind == 0) module->addAnd(NEW_ID, a, b, y);
        if (kind == 1) module->addOr(NEW_ID, a, b, y);
        if (kind == 2) module->addEq(NEW_ID, a, b, y);
        if (kind == 3) module->addNe(NEW_ID, a, b, y);
        return y;
    }

    bool rebuild(Record &x, Record &y, Record &z)
    {
        if (x.cell == y.cell || x.cell == z.cell || y.cell == z.cell ||
            x.complement || y.complement || !z.complement ||
            !compatible(x,y) || !compatible(x,z)) return false;
        int C = z.pred.values[0];
        if (std::find(y.pred.values.begin(), y.pred.values.end(), C) == y.pred.values.end() ||
            std::find(x.pred.values.begin(), x.pred.values.end(), C) != x.pred.values.end()) return false;
        int A = y.pred.values[0] == C ? y.pred.values[1] : y.pred.values[0];
        if (std::find(x.pred.values.begin(), x.pred.values.end(), A) == x.pred.values.end()) return false;
        int B = x.pred.values[0] == A ? x.pred.values[1] : x.pred.values[0];
        int delta = B ^ C;
        if (!delta || (delta & (delta-1))) return false;
        int pivot = 0;
        while (!(delta & (1 << pivot))) pivot++;
        if ((A & delta) || (C & delta) || !(B & delta)) return false;
        std::vector<int> group, fixed;
        int base = -1;
        for (int i = 0; i < GetSize(x.pred.control); i++) {
            if (i == pivot) continue;
            if ((A ^ C) & (1 << i)) {
                group.push_back(i);
                if (!(A & (1 << i)) && base < 0) base = i;
            } else fixed.push_back(i);
        }
        if (base < 0 || group.size() < 2 || group.size() > 4) return false;
        auto ctrl = x.pred.control;
        auto t = ctrl[pivot], b = ctrl[base];
        std::vector<int> needed;
        for (int i : fixed) {
            bool implied = false;
            for (auto g : x.guard) {
                if ((A & (1 << i)) && g == ctrl[i]) implied = true;
                auto d = driver(g);
                if (!(A & (1 << i)) && d && (d->type == ID($not) || d->type == ID($logic_not)) &&
                    sigmap(d->getPort(ID::A)) == SigSpec(ctrl[i])) implied = true;
            }
            if (!implied) needed.push_back(i);
        }
        if (needed.size() > 4) return false;

        // Complete mux boundary: outside the three decoded commands D=t.
        auto pmux = driver(z.cell->getPort(ID::D)[0]);
        if (!pmux || pmux->type != ID($pmux) || pmux->getParam(ID::WIDTH).as_int() != 1 ||
            sigmap(pmux->getPort(ID::A)) != SigSpec(t)) return false;
        pool<int> seen;
        for (auto s : pmux->getPort(ID::S)) {
            Predicate p;
            if (!predicate(s,p) || p.control != ctrl) return false;
            for (int v : p.values) {
                if ((v != A && v != B && v != C) || seen.count(v)) return false;
                seen.insert(v);
            }
        }
        if (!seen.count(A) || !seen.count(B)) return false;
        auto zd = z.cell->getPort(ID::D);
        if (!clean_cone(zd, ctrl) || !clean_cone(x.cell->getPort(ID::D), ctrl) ||
            !clean_cone(y.cell->getPort(ID::D), ctrl)) return false;
        if (evaluate(zd, ctrl, A) != SigSpec(State::S1) ||
            evaluate(zd, ctrl, B) != SigSpec(State::S1)) return false;

        auto xa = evaluate(x.cell->getPort(ID::D), ctrl, A);
        auto xb = evaluate(x.cell->getPort(ID::D), ctrl, B);
        auto ya = evaluate(y.cell->getPort(ID::D), ctrl, A);
        auto yc = evaluate(y.cell->getPort(ID::D), ctrl, C);
        auto xd = x.cell->getPort(ID::D), yd = y.cell->getPort(ID::D);
        int nx = 0, ny = 0;
        for (int i = 0; i < GetSize(xd); i++)
            if (xa[i] == State::S0 && xb[i] == State::S1) { xd[i] = t; nx++; }
        for (int i = 0; i < GetSize(yd); i++)
            if (ya[i] == State::S0 && yc[i] == State::S1) { yd[i] = b; ny++; }
        // Conservative profitability boundary: both banks must simplify.
        if (!nx || !ny) return false;

        // All validation above is read-only. Leave original shared cones intact.
        SigSpec o, e, guard;
        for (int i : needed) o.append((A & (1 << i)) ? SigSpec(ctrl[i]) : invert(ctrl[i]));
        for (int i : group) if (i != base)
            e.append(binary(b, ctrl[i], (A & (1 << i)) ? 3 : 2));
        for (auto g : x.guard) guard.append(g);
        auto h = binary(reduce(o), reduce(e), 0);
        auto g = reduce(guard);
        auto el = reduce(SigSpec({g[0], h[0], binary(t,b,2)[0]}));
        auto eh = reduce(SigSpec({g[0], h[0], invert(t)[0]}));
        auto dz = binary(t, binary(h, binary(invert(b), z.cell->getPort(ID::Q), 1), 0), 1);
        x.cell->setPort(ID::EN, el); x.cell->setPort(ID::D, xd);
        y.cell->setPort(ID::EN, eh); y.cell->setPort(ID::D, yd);
        z.cell->setPort(ID::EN, g); z.cell->setPort(ID::D, dz);
        log("6.1 ENABLE-FEEDBACK REBUILT %s, %s, %s (control=%d, group=%d).\n",
            log_id(x.cell), log_id(y.cell), log_id(z.cell), GetSize(ctrl), int(group.size()));
        return true;
    }

    int run()
    {
        std::vector<Record> records;
        for (auto c : module->selected_cells()) {
            Record r;
            if (record(c,r)) records.push_back(r);
            if (records.size() > 32) return 0;
        }
        int attempts = 0;
        for (auto &z : records) if (z.complement)
            for (auto &y : records) if (!y.complement && compatible(y,z))
                for (auto &x : records) if (!x.complement && compatible(x,z)) {
                    if (++attempts > 256) return 0;
                    if (rebuild(x,y,z)) return 1;
                }
        return 0;
    }
};

// Early arithmetic sharing from mutually exclusive decoded PMUX branches.
static void optimize_arithmetic_share(Design *design)
{
    constexpr bool low = false;
    constexpr bool all = true;
        // Sharing needs at least two arithmetic operators and a PMUX in one selected module.
        // A type-only precheck avoids constructing driver/user maps when impossible.
        bool possible=false;
        for(auto module:design->selected_modules()) {
            if(module->get_bool_attribute(ID::keep))continue;
            int ops=0;bool pm=false;
            for(auto c:module->selected_cells()) {
                if(c->get_bool_attribute(ID::keep))continue;
                ops+=(c->type==ID($add)||c->type==ID($sub));
                pm|=c->type==ID($pmux);
                if(ops>=2&&pm){possible=true;break;}
            }
            if(possible)break;
        }
        if(!possible){log("ARITH_SHARE total=0 all=%d\n",int(all));return;}
        CellTypes types(design);int total=0;
        for(auto module:design->selected_modules()) {
            if(module->get_bool_attribute(ID::keep))continue;
            SigMap sm(module);dict<SigBit,std::vector<Cell*>> drivers;dict<SigBit,pool<Cell*>> users;pool<SigBit> pinned;pool<Cell*> removed;
            for(auto w:module->wires())if(w->port_output||w->port_input||w->get_bool_attribute(ID::keep)||w->attributes.count(ID::init))for(auto b:sm(w))pinned.insert(b);
            for(auto c:module->cells())for(auto &p:c->connections())for(auto b:sm(p.second)) {
                if(!types.cell_known(c->type))pinned.insert(b);
                if(types.cell_output(c->type,p.first))drivers[b].push_back(c);
                if(types.cell_input(c->type,p.first))users[b].insert(c);
            }
            std::vector<Cell*> parents; for(auto c:module->selected_cells()) if(c->type==ID($pmux))parents.push_back(c);
            for(auto pmux:parents) {
                if(pmux->type!=ID($pmux)||pmux->get_bool_attribute(ID::keep))continue;
                int width=pmux->getParam(ID::WIDTH).as_int(),count=pmux->getParam(ID::S_WIDTH).as_int();
                if(width<1||width>64||count<2||count>8)continue;
                SigSpec s=sm(pmux->getPort(ID::S)),control;pool<int> values;std::vector<int> branch_values;bool valid=true;
                for(auto sb:s) {
                    if(!drivers.count(sb)||GetSize(drivers.at(sb))!=1){valid=false;break;}
                    Cell*d=drivers.at(sb)[0];if(removed.count(d)||d->get_bool_attribute(ID::keep)){valid=false;break;}
                    SigSpec signal;Const value;
                    if(d->type==ID($logic_not)){signal=sm(d->getPort(ID::A));value=Const(0,GetSize(signal));}
                    else if(d->type==ID($eq)) {
                        signal=sm(d->getPort(ID::A));SigSpec constant=sm(d->getPort(ID::B));
                        if(signal.is_fully_const())std::swap(signal,constant);
                        if(!constant.is_fully_const()||!constant.as_const().is_fully_def()||GetSize(signal)!=GetSize(constant)||d->getParam(ID::A_SIGNED).as_bool()||d->getParam(ID::B_SIGNED).as_bool()){valid=false;break;}
                        value=constant.as_const();
                    }else{valid=false;break;}
                    if(GetSize(signal)<2||GetSize(signal)>3){valid=false;break;}
                    for(auto bit:signal)if(bit.wire==nullptr)valid=false;
                    if(GetSize(control)==0)control=signal;
                    if(signal!=control||!values.insert(value.as_int()).second){valid=false;break;} branch_values.push_back(value.as_int());
                }
                if(!valid)continue;
                auto data_at=[&](int slot){return sm(slot==count?pmux->getPort(ID::A):pmux->getPort(ID::B).extract(slot*width,width));};
                auto private_op=[&](int slot)->Cell* {
                    SigSpec data=data_at(slot);if(GetSize(data)!=width||data[0].wire==nullptr||!drivers.count(data[0])||GetSize(drivers.at(data[0]))!=1)return nullptr;
                    Cell*c=drivers.at(data[0])[0];if(removed.count(c)||!module->selected(c)||c->get_bool_attribute(ID::keep)||(c->type!=ID($add)&&c->type!=ID($sub)))return nullptr;
                    if(c->getParam(ID::A_SIGNED).as_bool()||c->getParam(ID::B_SIGNED).as_bool()||GetSize(c->getPort(ID::A))!=width||GetSize(c->getPort(ID::B))!=width||sm(c->getPort(ID::Y))!=data)return nullptr;
                    SigSpec all_data=sm(pmux->getPort(ID::B));all_data.append(sm(pmux->getPort(ID::A)));
                    pool<SigBit> distinct;
                    for(auto bit:data){int occurrences=0;for(auto x:all_data)if(x==bit)occurrences++;
                        if(bit.wire==nullptr||pinned.count(bit)||!distinct.insert(bit).second||occurrences!=1||GetSize(drivers[bit])!=1||GetSize(users[bit])!=1||!users[bit].count(pmux))return nullptr;}
                    return c;
                };
                SigSpec default_select;pool<int> used;
                auto select_slot=[&](int slot)->SigSpec {
                    if(slot<count)return pmux->getPort(ID::S).extract(slot,1);
                    if(GetSize(default_select)==0){SigSpec any=module->ReduceOr(NEW_ID,pmux->getPort(ID::S));default_select=module->Not(NEW_ID,any);}
                    return default_select;
                };

                // The shared result is observed only under these two slots.
                // A raw address bit may distinguish them without decoding all bits.
                auto select_pair=[&](int target,int other)->SigSpec {
                    auto separates=[&](int bit,int polarity) {
                        bool seen_target=false,seen_other=false;
                        for(int address=0;address<(1<<GetSize(control));address++) {
                            int slot=count;
                            for(int k=0;k<count;k++)if(branch_values[k]==address){slot=k;break;}
                            if(slot==target){seen_target=true;if(((address>>bit)&1)!=polarity)return false;}
                            if(slot==other){seen_other=true;if(((address>>bit)&1)==polarity)return false;}
                        }
                        return seen_target&&seen_other;
                    };
                    for(int pass=0;pass<2;pass++)for(int bit=0;bit<GetSize(control);bit++) {
                        int actual_bit=low?pass:bit,polarity=low?bit:1-pass;
                        // Low-bit ordering is handled separately below.
                        if(low)break;
                        if(separates(actual_bit,polarity))return polarity?control.extract(actual_bit,1):module->Not(NEW_ID,control.extract(actual_bit,1));
                    }
                    if(low)for(int bit=0;bit<GetSize(control);bit++)for(int polarity=1;polarity>=0;polarity--)
                        if(separates(bit,polarity))return polarity?control.extract(bit,1):module->Not(NEW_ID,control.extract(bit,1));
                    return select_slot(target);
                };
                auto replace_slot=[&](int slot,SigSpec data){if(slot==count)pmux->setPort(ID::A,data);else{SigSpec v=pmux->getPort(ID::B);v.replace(slot*width,data);pmux->setPort(ID::B,v);}};
                auto table_mux=[&](const std::vector<SigSpec>& table) {
                    std::function<SigSpec(int,int)> build=[&](int bit,int prefix)->SigSpec {
                        if(bit==GetSize(control))return table[prefix];
                        SigSpec lo=build(bit+1,prefix),hi=build(bit+1,prefix|(1<<bit));
                        return lo==hi?lo:module->Mux(NEW_ID,lo,hi,control.extract(bit,1));
                    };
                    return build(0,0);
                };
                {
                    std::vector<int> slots;std::vector<Cell*> ops;
                    for(int slot=0;slot<=count;slot++) {
                        Cell*c=private_op(slot);if(!c)continue;
                        bool is_xor=c->type==ID($xor);
                        if(is_xor)continue;
                        slots.push_back(slot);ops.push_back(c);
                    }

                if(width>=4&&GetSize(ops)>=3) {
                    std::vector<SigSpec> left_table,right_table,mode_table;
                    for(int address=0;address<(1<<GetSize(control));address++) {
                        int slot=count;for(int k=0;k<count;k++)if(branch_values[k]==address){slot=k;break;}
                        Cell*op=ops[0];for(int k=0;k<GetSize(ops);k++)if(slots[k]==slot){op=ops[k];break;}
                        left_table.push_back(sm(op->getPort(ID::A)));right_table.push_back(sm(op->getPort(ID::B)));
                        mode_table.push_back(SigSpec(op->type==ID($sub)?State::S1:State::S0));
                    }
                    SigSpec left=table_mux(left_table),right=table_mux(right_table),result=module->addWire(NEW_ID,width);
                    bool has_add=false,has_sub=false;for(auto op:ops){has_add|=op->type==ID($add);has_sub|=op->type==ID($sub);}
                    if(!has_sub)module->addAdd(NEW_ID,left,right,result);
                    else if(!has_add)module->addSub(NEW_ID,left,right,result);
                    else {
                        SigSpec mode=table_mux(mode_table);Cell*alu=module->addCell(NEW_ID,ID($alu));
                        alu->setParam(ID::A_SIGNED,0);alu->setParam(ID::B_SIGNED,0);alu->setParam(ID::A_WIDTH,width);alu->setParam(ID::B_WIDTH,width);alu->setParam(ID::Y_WIDTH,width);
                        alu->setPort(ID::A,left);alu->setPort(ID::B,right);alu->setPort(ID::BI,mode);alu->setPort(ID::CI,mode);alu->setPort(ID::Y,result);alu->setPort(ID::X,module->addWire(NEW_ID,width));alu->setPort(ID::CO,module->addWire(NEW_ID,width));
                    }
                    for(int k=0;k<GetSize(ops);k++){replace_slot(slots[k],result);removed.insert(ops[k]);module->remove(ops[k]);}
                    total++;log("ARITH_SHARE width=%d mixed=%d slots=%d group=%d family=%d\n",width,int(has_add&&has_sub),slots[0],GetSize(ops),0);
                    continue;
                }
                }
                for(int i=0;i<=count;i++) {
                    if(used.count(i))continue;Cell*c0=private_op(i);if(!c0)continue;
                    for(int j=count;j>i;j--) {
                        if(used.count(j))continue;Cell*c1=private_op(j);if(!c1||c1==c0)continue;
                        bool mixed=c0->type!=c1->type;if(!mixed&&!all)continue;
                        SigSpec a0=sm(c0->getPort(ID::A)),b0=sm(c0->getPort(ID::B)),a1=sm(c1->getPort(ID::A)),b1=sm(c1->getPort(ID::B));
                        SigSpec result,left,right;bool found=false;SigSpec choose;
                        if(mixed) {
                            Cell*add=c0->type==ID($add)?c0:c1;Cell*sub=c0->type==ID($sub)?c0:c1;
                            SigSpec aa=sm(add->getPort(ID::A)),ab=sm(add->getPort(ID::B)),sa=sm(sub->getPort(ID::A)),sb=sm(sub->getPort(ID::B));
                            SigSpec addother,subother,common;bool common_right=false;
                            if(sb==aa){common=sb;addother=ab;subother=sa;common_right=true;found=true;}
                            else if(sb==ab){common=sb;addother=aa;subother=sa;common_right=true;found=true;}
                            else if(sa==aa){common=sa;addother=ab;subother=sb;found=true;}
                            else if(sa==ab){common=sa;addother=aa;subother=sb;found=true;}
                            if(!found&&width<4)continue;
                            if(!found){found=true;result=module->addWire(NEW_ID,width);choose=select_pair(c0==sub?i:j,c0==sub?j:i);
                                left=module->Mux(NEW_ID,aa,sa,choose);right=module->Mux(NEW_ID,ab,sb,choose);
                                Cell*alu=module->addCell(NEW_ID,ID($alu));alu->setParam(ID::A_SIGNED,0);alu->setParam(ID::B_SIGNED,0);alu->setParam(ID::A_WIDTH,width);alu->setParam(ID::B_WIDTH,width);alu->setParam(ID::Y_WIDTH,width);
                                alu->setPort(ID::A,left);alu->setPort(ID::B,right);alu->setPort(ID::BI,choose);alu->setPort(ID::CI,choose);alu->setPort(ID::Y,result);alu->setPort(ID::X,module->addWire(NEW_ID,width));alu->setPort(ID::CO,module->addWire(NEW_ID,width));
                            } else {result=module->addWire(NEW_ID,width);choose=select_pair(c0==sub?i:j,c0==sub?j:i);SigSpec variable=module->Mux(NEW_ID,addother,subother,choose);
                                left=common_right?variable:common;right=common_right?common:variable;
                                Cell*alu=module->addCell(NEW_ID,ID($alu));alu->setParam(ID::A_SIGNED,0);alu->setParam(ID::B_SIGNED,0);alu->setParam(ID::A_WIDTH,width);alu->setParam(ID::B_WIDTH,width);alu->setParam(ID::Y_WIDTH,width);
                                alu->setPort(ID::A,left);alu->setPort(ID::B,right);alu->setPort(ID::BI,choose);alu->setPort(ID::CI,choose);alu->setPort(ID::Y,result);alu->setPort(ID::X,module->addWire(NEW_ID,width));alu->setPort(ID::CO,module->addWire(NEW_ID,width));}
                        } else {
                            SigSpec common,other0,other1;bool right_common=false;
                            if(b0==b1){common=b0;other0=a0;other1=a1;right_common=true;found=true;}
                            else if(a0==a1){common=a0;other0=b0;other1=b1;found=true;}
                            else if(c0->type==ID($add)&&a0==b1){common=a0;other0=b0;other1=a1;found=true;}
                            else if(c0->type==ID($add)&&b0==a1){common=b0;other0=a0;other1=b1;right_common=true;found=true;}
                            if(!found&&width<4)continue;
                            if(!found){found=true;result=module->addWire(NEW_ID,width);choose=select_pair(j,i);
                                left=module->Mux(NEW_ID,a0,a1,choose);right=module->Mux(NEW_ID,b0,b1,choose);
                                if(c0->type==ID($add))module->addAdd(NEW_ID,left,right,result);else module->addSub(NEW_ID,left,right,result);
                            } else {result=module->addWire(NEW_ID,width);choose=select_pair(j,i);SigSpec variable=module->Mux(NEW_ID,other0,other1,choose);left=right_common?variable:common;right=right_common?common:variable;
                                if(c0->type==ID($add))module->addAdd(NEW_ID,left,right,result);else module->addSub(NEW_ID,left,right,result);}
                        }
                        if(!found)continue;
                        replace_slot(i,result);replace_slot(j,result);used.insert(i);used.insert(j);
                        removed.insert(c0);removed.insert(c1);module->remove(c0);module->remove(c1);total++;
                        log("ARITH_SHARE width=%d mixed=%d slots=%d,%d\n",width,int(mixed),i,j);break;
                    }
                }
            }
        }
        log("ARITH_SHARE total=%d all=%d\n",total,int(all));

}


static std::pair<int,int> optimize_priority_mux(RTLIL::Module *module)
{
int total_h3_candidates=0,total_h3_rebuilt=0;
    if (module->get_bool_attribute(ID::keep)) return {0,0};

            std::vector<RTLIL::Cell *> h3_muxes;

            for (auto cell : module->cells())
            {
                if (cell->type != ID($mux) || !module->selected(cell) || cell->get_bool_attribute(ID::keep))
                    continue;

                int width =
                    cell->getParam(ID::WIDTH).as_int();

                const RTLIL::SigSpec &a = cell->getPort(ID::A);

                const RTLIL::SigSpec &b = cell->getPort(ID::B);

                const RTLIL::SigSpec &sel = cell->getPort(ID::S);

                const RTLIL::SigSpec &y = cell->getPort(ID::Y);

                if (width <= 0)
                    continue;

                if (GetSize(a) != width ||
                    GetSize(b) != width ||
                    GetSize(y) != width ||
                    GetSize(sel) != 1)
                    continue;

                h3_muxes.push_back(cell);
            }

            // 5.1 requires depth >= 3. SigMap preserves signal widths, so
            // the existing port-shape filter needs no canonicalization.
            // This is the last analysis in the module; skip it when no
            // three-cell chain can exist, before building the full map.
            if (h3_muxes.size() < 3)
                return {0,0};

            SigMap h3_sigmap(module);

            // Index original canonical vectors; defer deletion until the scan ends.
            // preserve all drivers so ambiguous child matches still reject.
            dict<RTLIL::SigSpec, std::vector<RTLIL::Cell *>> h3_by_a, h3_by_y;
            for (auto cell : h3_muxes) {
                h3_by_a[h3_sigmap(cell->getPort(ID::A))].push_back(cell);
                h3_by_y[h3_sigmap(cell->getPort(ID::Y))].push_back(cell);
            }

            /*
             * 当前 mux 的 Y 如果接到另一个 mux 的 A，
             * 那它就不是整条链最靠近输出的一层。
             */
            auto h3_has_parent =
                [&](RTLIL::Cell *cell) -> bool
            {
                RTLIL::SigSpec y =
                    h3_sigmap(
                        cell->getPort(ID::Y));

                auto it = h3_by_a.find(y);
                if (it != h3_by_a.end())
                    for (auto other : it->second)
                        if (other != cell)
                            return true;

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
                ambiguous = false;
                if (GetSize(a) != width) return nullptr;
                auto it = h3_by_y.find(a);
                if (it == h3_by_y.end()) return nullptr;
                ambiguous = it->second.size() > 1;
                return ambiguous ? nullptr : it->second.front();
            };



            // Build input users only when a chain reaches the privacy check.
            // Invalidate after a rewrite because selector ports and new gates
            // change consumers. Canonical bit keys retain partial overlaps.
            using H3User = std::pair<RTLIL::Cell *, RTLIL::IdString>;
            dict<RTLIL::SigBit, pool<H3User>> h3_users;
            pool<RTLIL::SigBit> h3_output_bits;
            pool<RTLIL::SigBit> h3_preserved_bits;
            for (auto wire : module->wires())
                if (wire->get_bool_attribute(ID::keep) || wire->attributes.count(ID::init))
                    for (auto bit : h3_sigmap(RTLIL::SigSpec(wire))) h3_preserved_bits.insert(bit);
            bool h3_users_ready = false;
            auto h3_prepare_users = [&]() {
                if (h3_users_ready) return;
                h3_users.clear();
                h3_output_bits.clear();
                for (auto cell : module->cells())
                    for (auto &port : cell->connections()) if (cell->input(port.first))
                        for (auto bit : h3_sigmap(port.second))
                            h3_users[bit].insert(H3User(cell, port.first));
                for (auto wire : module->wires()) if (wire->port_output)
                    for (auto bit : h3_sigmap(RTLIL::SigSpec(wire))) h3_output_bits.insert(bit);
                h3_users_ready = true;
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

                h3_prepare_users();
                bool saw_expected_parent = false;
                for (auto bit : y) {
                    if (h3_output_bits.count(bit) || h3_preserved_bits.count(bit)) return false;
                    auto it = h3_users.find(bit);
                    if (it == h3_users.end()) continue;
                    for (auto &user : it->second) {
                        if (user.first != parent || user.second != ID::A) return false;
                        saw_expected_parent = true;
                    }
                }
                return saw_expected_parent && h3_sigmap(parent->getPort(ID::A)) == y;
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


            pool<RTLIL::Cell *> h3_removed;
            for (auto start : h3_muxes)
            {
                if (h3_removed.count(start)) continue;
                /*
                 * 只从最高优先级、最靠近输出的一层开始，
                 * 防止同一条链重复报告。
                 */
                if (h3_has_parent(start))
                    continue;

                int width =
                    start->getParam(ID::WIDTH).as_int();

                std::vector<RTLIL::Cell *> chain;
                pool<RTLIL::SigBit> selectors;
                pool<RTLIL::Cell *> visited;

                bool valid = true;
                RTLIL::Cell *current = start;

                while (current != nullptr)
                {
                    if (!visited.insert(current).second)
                    {
                        valid = false;
                        break;
                    }


                    chain.push_back(current);


                    RTLIL::SigSpec sel =
                        h3_sigmap(
                            current->getPort(ID::S));

                    if (GetSize(sel) != 1)
                    {
                        valid = false;
                        break;
                    }

                    if (!selectors.insert(sel[0]).second)
                    {
                        valid = false;
                        break;
                    }




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
                // Experimental two-entry priority groups. Preserve high-to-low order.
                if (chain.back()->getPort(ID::A).is_fully_zero() && chain.size() >= 4) {
                    RTLIL::SigSpec accum = RTLIL::Const(0, width);
                    for (int end = int(chain.size()); end > 0; end -= 2) {
                        int begin = std::max(0, end - 2);
                        auto high_s = original_selectors[begin];
                        RTLIL::SigSpec high_mask;
                        for (int bit = 0; bit < width; bit++) high_mask.append(high_s);
                        auto group = module->And(NEW_ID, chain[begin]->getPort(ID::B), high_mask);
                        RTLIL::SigSpec any = high_s;
                        if (begin + 1 < end) {
                            auto low_s = original_selectors[begin + 1];
                            auto exclusive = module->And(NEW_ID, module->Not(NEW_ID, high_s), low_s);
                            RTLIL::SigSpec low_mask;
                            for (int bit = 0; bit < width; bit++) low_mask.append(exclusive);
                            auto term = module->And(NEW_ID, chain[begin + 1]->getPort(ID::B), low_mask);
                            group = module->Or(NEW_ID, group, term);
                            any = module->Or(NEW_ID, high_s, low_s);
                        }
                        accum = module->Mux(NEW_ID, accum, group, any);
                    }
                    module->connect(start->getPort(ID::Y), accum);
                    for (auto mux : chain) h3_removed.insert(mux);
                    total_h3_rebuilt++;
                    h3_users_ready = false;
                    continue;
                }
                RTLIL::SigSpec data, select;
                RTLIL::SigSpec base = chain.back()->getPort(ID::A);
                RTLIL::SigSpec prefix = h3_make_not(original_selectors[0]);
                for (size_t k = 0; k < chain.size(); k++) {
                    data.append(chain[k]->getPort(ID::B));
                    select.append(k == 0 ? original_selectors[0] :
                                  h3_make_and(prefix, original_selectors[k]));
                    if (k > 0 && k + 1 < chain.size())
                        prefix = h3_make_and(prefix, h3_make_not(original_selectors[k]));
                }
                if (base.is_fully_zero()) {
                    // The zero default contributes no data term. Construct
                    // only the exclusive products; no default-enable tree.
                    RTLIL::SigSpec accum;
                    for (int k = 0; k < GetSize(select); k++) {
                        RTLIL::SigSpec mask;
                        for (int bit = 0; bit < width; bit++) mask.append(select[k]);
                        auto term = module->addWire(NEW_ID, width);
                        module->addAnd(NEW_ID, data.extract(k * width, width), mask, term);
                        if (k == 0) accum = RTLIL::SigSpec(term);
                        else {
                            auto sum = module->addWire(NEW_ID, width);
                            module->addOr(NEW_ID, accum, term, sum);
                            accum = RTLIL::SigSpec(sum);
                        }
                    }
                    module->connect(start->getPort(ID::Y), accum);
                    h3_removed.insert(start);
                } else {
                    start->type = ID($pmux);
                    start->setParam(ID::S_WIDTH, GetSize(select));
                    start->setPort(ID::A, base);
                    start->setPort(ID::B, data);
                    start->setPort(ID::S, select);
                }
                for (size_t k = 1; k < chain.size(); k++)
                    h3_removed.insert(chain[k]);

                total_h3_rebuilt++;
                h3_users_ready = false;

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
for (auto cell : h3_removed) module->remove(cell);
return {total_h3_candidates,total_h3_rebuilt};
}

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
        log("    pmux_opt [-arith] [selection]\n");
        log("    -arith: mutually exclusive arithmetic sharing before coarse PMUX rewrites.\n");
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
        if (args.size() > 1 && args[1] == "-arith") {
            extra_args(args, 2, design);
            log_header(design, "Executing PMUX_OPT arithmetic sharing.\n");
            optimize_arithmetic_share(design);
            return;
        }
        if (args.size() > 1 && args[1] == "-lut")
            log_cmd_error("The post-ABC -lut mode was removed under competition clarification C147.1.\n");
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
            bool has_pmux = false;

            for (auto cell : module->cells())
                if (cell->type == ID($pmux)) {
                    has_pmux = true;
                    break;
                }

            if (has_pmux)
            {
            SigMap sigmap(module);

            /*
             * Pattern C 使用：
             * 在 selector 已知 control == CONST 的前提下，
             * 对 branch 数据锥进行条件常量传播。
             *
             * 其他未知输入保留为符号信号；不能用 X===X
             * 推导两个独立未知输入恒等。
             */
            std::unique_ptr<ConstEval> branch_consteval;

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
            bool has_feedback_target = false;

            for (auto driver_cell : module->cells())
            {
                // 6.1 needs a one-bit, positive-enable DFFE for Z.
                // Reuse this scan and avoid initial-state/guard analysis
                // when no selected cell can satisfy that necessary condition.
                if (!has_feedback_target && driver_cell->type == ID($dffe) &&
                    module->selected(driver_cell) && !driver_cell->get_bool_attribute(ID::keep) &&
                    driver_cell->getParam(ID::EN_POLARITY).as_bool() &&
                    driver_cell->getParam(ID::WIDTH).as_int() == 1 &&
                    GetSize(driver_cell->getPort(ID::D)) == 1 &&
                    GetSize(driver_cell->getPort(ID::Q)) == 1 &&
                    GetSize(driver_cell->getPort(ID::CLK)) == 1 &&
                    GetSize(driver_cell->getPort(ID::EN)) == 1)
                    has_feedback_target = true;

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
            log("Total enable-feedback rebuilt: %d\n",
                has_feedback_target ? EnableFeedback(module, sigmap, driver_map, multi_driver_bits).run() : 0);
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
                        // Constant branches need no conditional propagation,
                        // including existing X/Z bits, which remain untouched.
                        if (raw_branch.is_fully_const()) {
                            new_port_b.append(raw_branch);
                            continue;
                        }

                        if (!branch_consteval)
                            branch_consteval.reset(new ConstEval(module));
                        branch_consteval->clear();

                        branch_consteval->set(
                            info.control,
                            cond.value);

                        RTLIL::SigSpec evaluated_branch =
                            raw_branch;

                        RTLIL::SigSpec undef;

                        bool eval_ok =
                            branch_consteval->eval(
                                evaluated_branch,
                                undef);

                        /*
                         * eval 失败时完全保持原 branch。
                         *
                         * 未确定的外部输入保持为独立符号；若求值失败，
                         * 整个分支保持原样，包括混合数据分支。
                         * 成功时只替换可确定的 0/1 位，X/Z 位仍保留原信号。
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
                     * helper
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
                     * ==================================================
                     * Binary indexed pair selection.
                     *
                     * pair_index = control with swap_bit removed.
                     * Each ordinary pair contributes one shared data
                     * value.  A special pair first resolves its two
                     * exceptional values with swap_bit, then enters the
                     * same binary tree.  The final cross-lane swap below
                     * remains unchanged.
                     * ==================================================
                     */
                    RTLIL::SigSpec swap_bit =
                        info_a.control.extract(
                            candidate.swap_bit,
                            1);

                    RTLIL::SigSpec pair_index;

                    for (int bit = 0;
                         bit < info_a.ctrl_width;
                         bit++)
                    {
                        if (bit == candidate.swap_bit)
                            continue;

                        pair_index.append(
                            info_a.control.extract(bit, 1));
                    }

                    log_assert(
                        pair_index.size() ==
                        info_a.ctrl_width - 1);

                    log_assert(
                        pair_count ==
                        (1 << pair_index.size()));

                    std::vector<RTLIL::SigSpec> pair_x_values(
                        pair_count);

                    std::vector<RTLIL::SigSpec> pair_y_values(
                        pair_count);

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

                        /*
                         * Remove swap_bit from the binary control value.
                         * The result is the exact index used by pair_index.
                         */
                        int pair_slot = 0;
                        int pair_slot_bit = 0;

                        for (int bit = 0;
                             bit < info_a.ctrl_width;
                             bit++)
                        {
                            if (bit == candidate.swap_bit)
                                continue;

                            if ((base_value >> bit) & 1)
                                pair_slot |=
                                    (1 << pair_slot_bit);

                            pair_slot_bit++;
                        }

                        log_assert(
                            pair_slot_bit ==
                            pair_index.size());

                        log_assert(
                            pair_slot >= 0 &&
                            pair_slot < pair_count);

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

                        log_assert(a_base_branch >= 0);
                        log_assert(b_base_branch >= 0);
                        log_assert(a_mate_branch >= 0);
                        log_assert(b_mate_branch >= 0);

                        bool special = false;

                        for (int v :
                             candidate.special_base_values)
                            if (v == base_value)
                                special = true;

                        if (special)
                        {
                            RTLIL::SigSpec x_base =
                                info_a.port_b.extract(
                                    a_base_branch * width,
                                    width);

                            RTLIL::SigSpec x_mate =
                                info_b.port_b.extract(
                                    b_mate_branch * width,
                                    width);

                            RTLIL::SigSpec y_base =
                                info_b.port_b.extract(
                                    b_base_branch * width,
                                    width);

                            RTLIL::SigSpec y_mate =
                                info_a.port_b.extract(
                                    a_mate_branch * width,
                                    width);

                            pair_x_values[pair_slot] =
                                make_mux(
                                    x_base,
                                    x_mate,
                                    swap_bit);

                            pair_y_values[pair_slot] =
                                make_mux(
                                    y_base,
                                    y_mate,
                                    swap_bit);
                        }
                        else
                        {
                            pair_x_values[pair_slot] =
                                info_b.port_b.extract(
                                    b_mate_branch * width,
                                    width);

                            pair_y_values[pair_slot] =
                                info_a.port_b.extract(
                                    a_mate_branch * width,
                                    width);
                        }
                    }

                    for (int slot = 0;
                         slot < pair_count;
                         slot++)
                    {
                        log_assert(
                            pair_x_values[slot].size() == width);

                        log_assert(
                            pair_y_values[slot].size() == width);
                    }

                    auto make_binary_indexed_mux =
                        [&](std::vector<RTLIL::SigSpec> values)
                        -> RTLIL::SigSpec
                    {
                        log_assert(
                            int(values.size()) == pair_count);

                        for (int level = 0;
                             level < pair_index.size();
                             level++)
                        {
                            std::vector<RTLIL::SigSpec> next;

                            log_assert(
                                (values.size() & 1) == 0);

                            for (int index = 0;
                                 index < int(values.size());
                                 index += 2)
                            {
                                next.push_back(
                                    make_mux(
                                        values[index],
                                        values[index + 1],
                                        pair_index.extract(
                                            level, 1)));
                            }

                            values.swap(next);
                        }

                        log_assert(values.size() == 1);
                        return values[0];
                    };

                    RTLIL::SigSpec pair_x =
                        make_binary_indexed_mux(
                            pair_x_values);

                    RTLIL::SigSpec pair_y =
                        make_binary_indexed_mux(
                            pair_y_values);


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
 * Pattern E / 3.2:
 *
 * 同前缀比较器因式分解
 *
 * v1 只处理：
 *
 *   - 两个 unsigned $eq
 *   - 两边等宽
 *   - 比较同一个 signal
 *   - 另一边均为纯 0/1 常量
 *   - 两个常量恰好只有 1 bit 不同
 *   - comparator width >= 7
 *
 * 原：
 *
 *   eq0 = (signal == CONST0)
 *   eq1 = (signal == CONST1)
 *
 * 若 CONST0 / CONST1 只有 bit[k] 不同：
 *
 *   common = (signal_without_k == common_constant)
 *   eq0    = common & match(signal[k], CONST0[k])
 *   eq1    = common & match(signal[k], CONST1[k])
 *
 * 该变换为全局逻辑等价，不依赖 downstream guard。
 * ==================================================
 */

int pattern_e_candidates = 0;

auto pattern_e_extract_eq =
    [&](RTLIL::Cell *cell,
        RTLIL::SigSpec &signal,
        RTLIL::Const &constant)
    -> bool
{
    if (cell->type != ID($eq))
        return false;

    int a_width =
        cell->getParam(ID::A_WIDTH).as_int();

    int b_width =
        cell->getParam(ID::B_WIDTH).as_int();

    bool a_signed =
        cell->getParam(ID::A_SIGNED).as_bool();

    bool b_signed =
        cell->getParam(ID::B_SIGNED).as_bool();

    if (a_signed ||
        b_signed ||
        a_width != b_width ||
        a_width < 7)
        return false;

    RTLIL::SigSpec a =
        sigmap(cell->getPort(ID::A));

    RTLIL::SigSpec b =
        sigmap(cell->getPort(ID::B));

    if (!a.is_fully_const() &&
        b.is_fully_const())
    {
        signal = a;
        constant = b.as_const();
    }
    else if (
        a.is_fully_const() &&
        !b.is_fully_const())
    {
        signal = b;
        constant = a.as_const();
    }
    else
    {
        return false;
    }

    if (signal.size() != a_width ||
        constant.size() != a_width)
        return false;

    if (cell->getParam(ID::Y_WIDTH).as_int() != 1)
        return false;

    /*
     * X/Z 常量不参与 v1。
     */
    for (int bit = 0;
         bit < constant.size();
         bit++)
    {
        if (constant[bit] != RTLIL::State::S0 &&
            constant[bit] != RTLIL::State::S1)
            return false;
    }

    return true;
};


std::vector<RTLIL::Cell *> pattern_e_eqs;

for (auto cell : module->cells())
{
    if (cell->type == ID($eq))
        pattern_e_eqs.push_back(cell);
}

pool<RTLIL::Cell *> pattern_e_used;


for (size_t i = 0;
     i < pattern_e_eqs.size();
     i++)
{
    RTLIL::Cell *eq0 =
        pattern_e_eqs[i];

    if (pattern_e_used.count(eq0))
        continue;

    RTLIL::SigSpec signal0;
    RTLIL::Const constant0;

    if (!pattern_e_extract_eq(
            eq0,
            signal0,
            constant0))
        continue;


    for (size_t j = i + 1;
         j < pattern_e_eqs.size();
         j++)
    {
        RTLIL::Cell *eq1 =
            pattern_e_eqs[j];

        if (pattern_e_used.count(eq1))
            continue;

        RTLIL::SigSpec signal1;
        RTLIL::Const constant1;

        if (!pattern_e_extract_eq(
                eq1,
                signal1,
                constant1))
            continue;

        /*
         * 必须比较同一个 canonical signal。
         */
        if (signal0 != signal1)
            continue;

        if (constant0.size() !=
            constant1.size())
            continue;


        int different_bit = -1;
        bool multiple_differences = false;

        for (int bit = 0;
             bit < constant0.size();
             bit++)
        {
            if (constant0[bit] ==
                constant1[bit])
                continue;

            if (different_bit >= 0)
            {
                multiple_differences = true;
                break;
            }

            different_bit = bit;
        }

        if (multiple_differences ||
            different_bit < 0)
            continue;


        RTLIL::SigSpec common_signal;
        RTLIL::Const common_constant;

        for (int bit = 0;
             bit < signal0.size();
             bit++)
        {
            if (bit == different_bit)
                continue;

            common_signal.append(
                signal0.extract(bit, 1));

            common_constant.append(
                RTLIL::Const(
                    constant0[bit],
                    1));
        }

        if (common_signal.size() !=
                signal0.size() - 1 ||
            common_constant.size() !=
                signal0.size() - 1)
        {
            log_error(
                "Pattern E internal width mismatch.\n");
        }


        RTLIL::SigSpec old_y0 =
            eq0->getPort(ID::Y);

        RTLIL::SigSpec old_y1 =
            eq1->getPort(ID::Y);

        if (old_y0.size() != 1 ||
            old_y1.size() != 1)
            continue;

        if (sigmap(old_y0) ==
            sigmap(old_y1))
            continue;


        RTLIL::SigSpec differing_signal =
            signal0.extract(
                different_bit,
                1);


        RTLIL::Wire *common_eq_wire =
            module->addWire(NEW_ID);

        RTLIL::Wire *not_bit_wire =
            module->addWire(NEW_ID);


        module->addEq(
            NEW_ID,
            common_signal,
            common_constant,
            RTLIL::SigSpec(
                common_eq_wire));


        module->addNot(
            NEW_ID,
            differing_signal,
            RTLIL::SigSpec(
                not_bit_wire));


        RTLIL::SigSpec match0 =
            constant0[different_bit] ==
                    RTLIL::State::S1
                ? differing_signal
                : RTLIL::SigSpec(
                      not_bit_wire);

        RTLIL::SigSpec match1 =
            constant1[different_bit] ==
                    RTLIL::State::S1
                ? differing_signal
                : RTLIL::SigSpec(
                      not_bit_wire);


        /*
         * 先记录名称用于日志，
         * 再删除旧 comparator。
         */
        RTLIL::IdString old_name0 =
            eq0->name;

        RTLIL::IdString old_name1 =
            eq1->name;

        pattern_e_used.insert(eq0);
        pattern_e_used.insert(eq1);

        module->remove(eq0);
        module->remove(eq1);


        /*
         * 新逻辑直接驱动原 comparator 的 Y，
         * 因此所有 downstream PMUX / control logic
         * 无需修改。
         */
        module->addAnd(
            NEW_ID,
            RTLIL::SigSpec(
                common_eq_wire),
            match0,
            old_y0);

        module->addAnd(
            NEW_ID,
            RTLIL::SigSpec(
                common_eq_wire),
            match1,
            old_y1);


        pattern_e_candidates++;

        log("\n");
        log("COMMON-PREFIX EQ REWRITE\n");
        log("  eq0         : %s\n",
            log_id(old_name0));
        log("  eq1         : %s\n",
            log_id(old_name1));
        log("  old width   : %d\n",
            signal0.size());
        log("  shared width: %d\n",
            common_signal.size());
        log("  differing bit: %d\n",
            different_bit);

        /*
         * 一个 comparator 只参加一次配对。
         */
        break;
    }
}


if (pattern_e_candidates > 0)
{
    log("\n");
    log(
        "Pattern E candidates in module %s: %d\n",
        log_id(module),
        pattern_e_candidates);
}


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
            auto result = optimize_priority_mux(module);
            total_h3_candidates += result.first;
            total_h3_rebuilt += result.second;
        }

        }


        log("\n");

        log("Total 8.1 decoded PMUX rebuilt: %d\n", optimize_decoded_pmux(design));

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
