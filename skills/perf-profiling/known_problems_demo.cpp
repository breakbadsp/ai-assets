// Calibration program for profilers: each tool must find its planted problem
// here before you trust a clean result from it on real code.
//
//   g++ -std=c++26 -O2 -g -fno-omit-frame-pointer known_problems_demo.cpp -o demo
//
// Planted problems and the tool that must find each one:
//   1. Array-of-structs scan that uses 8 of each 64 bytes (cache misses):
//      cachegrind puts almost all D1 misses on the ScanQuantities line;
//      perf stat shows a high L1-dcache-load-misses count.
//   2. One heap allocation for each item (allocation churn):
//      heaptrack reports 200,000 temporary allocations from MakeLine.
//   3. One system call for each item (no batching):
//      strace -c reports about 200,000 write calls.
#include <cstdio>
#include <memory>
#include <string>
#include <unistd.h>
#include <vector>

namespace
{

struct Order
{
  long id_ = 0;
  double price_ = 0;
  long qty_ = 0;
  char other_fields_[40] = {};
};

constexpr std::size_t kOrders = 4'000'000;
constexpr int kScans = 20;
constexpr int kItems = 200'000;

long ScanQuantities(const std::vector<Order> &p_orders)
{
  long total = 0;
  for (int scan = 0; scan < kScans; ++scan)
  {
    for (const Order &order : p_orders)
    {
      total += order.qty_; // problem 1: one cache line for each 8 bytes used
    }
  }
  return total;
}

std::unique_ptr<std::string> MakeLine(int p_item)
{
  return std::make_unique<std::string>(std::to_string(p_item) + "\n"); // problem 2
}

} // namespace

int main()
{
  std::vector<Order> orders(kOrders);
  for (std::size_t i = 0; i < orders.size(); ++i)
  {
    orders[i].qty_ = static_cast<long>(i % 7);
  }
  const long total = ScanQuantities(orders);
  std::size_t bytes = 0;
  for (int item = 0; item < kItems; ++item)
  {
    const std::unique_ptr<std::string> line = MakeLine(item);
    bytes += line->size();
    static_cast<void>(!::write(2, line->data(), 0)); // problem 3: one system call each
  }
  std::printf("%ld %zu\n", total, bytes);
}
