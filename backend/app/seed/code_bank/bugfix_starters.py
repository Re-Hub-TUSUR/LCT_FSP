"""The «найди ошибку» starters in compiled languages: task key → compiler id → code.

Each repeats the mistake of the Python starter of its task. The builder runs only Python, so
these were checked on the code runner itself: the starter fails every hidden group and the same
program with the mistake fixed passes all of them. Check a new one the same way.
"""

JAVA = "openjdk-25"
CPP = "g++-15"
CSHARP = "dotnet-csharp-9"
GO = "go-1.26"

COUNT_BELOW = {
    JAVA: """import java.io.*;
import java.util.*;

public class Main {
    static int countBelow(int[] values, int x) {
        int lo = 0, hi = values.length - 1;
        while (lo < hi) {
            int mid = (lo + hi) / 2;
            if (values[mid] < x) lo = mid + 1;
            else hi = mid;
        }
        return lo;
    }

    public static void main(String[] args) throws IOException {
        StreamTokenizer in = new StreamTokenizer(new BufferedReader(new InputStreamReader(System.in)));
        in.nextToken();
        int n = (int) in.nval;
        int[] values = new int[n];
        for (int i = 0; i < n; i++) {
            in.nextToken();
            values[i] = (int) in.nval;
        }
        in.nextToken();
        int q = (int) in.nval;
        long total = 0;
        for (int i = 0; i < q; i++) {
            in.nextToken();
            total += countBelow(values, (int) in.nval);
        }
        System.out.println(total);
    }
}
""",
    CPP: """#include <bits/stdc++.h>
using namespace std;

int countBelow(const vector<int>& values, int x) {
    int lo = 0, hi = (int)values.size() - 1;
    while (lo < hi) {
        int mid = (lo + hi) / 2;
        if (values[mid] < x) lo = mid + 1;
        else hi = mid;
    }
    return lo;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    vector<int> values(n);
    for (int& value : values) cin >> value;
    int q;
    cin >> q;
    long long total = 0;
    for (int i = 0; i < q; i++) {
        int x;
        cin >> x;
        total += countBelow(values, x);
    }
    cout << total << "\\n";
    return 0;
}
""",
    CSHARP: """using System;

var data = Console.In.ReadToEnd().Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries);
int n = int.Parse(data[0]);
var values = new int[n];
for (int i = 0; i < n; i++) values[i] = int.Parse(data[1 + i]);
int q = int.Parse(data[1 + n]);
long total = 0;
for (int i = 0; i < q; i++) total += CountBelow(values, int.Parse(data[2 + n + i]));
Console.WriteLine(total);

static int CountBelow(int[] values, int x)
{
    int lo = 0, hi = values.Length - 1;
    while (lo < hi)
    {
        int mid = (lo + hi) / 2;
        if (values[mid] < x) lo = mid + 1;
        else hi = mid;
    }
    return lo;
}
""",
    GO: """package main

import (
	"bufio"
	"fmt"
	"os"
)

func countBelow(values []int, x int) int {
	lo, hi := 0, len(values)-1
	for lo < hi {
		mid := (lo + hi) / 2
		if values[mid] < x {
			lo = mid + 1
		} else {
			hi = mid
		}
	}
	return lo
}

func main() {
	in := bufio.NewReader(os.Stdin)
	var n int
	fmt.Fscan(in, &n)
	values := make([]int, n)
	for i := range values {
		fmt.Fscan(in, &values[i])
	}
	var q int
	fmt.Fscan(in, &q)
	total := 0
	for i := 0; i < q; i++ {
		var x int
		fmt.Fscan(in, &x)
		total += countBelow(values, x)
	}
	fmt.Println(total)
}
""",
}

ALERT_REPEATS = {
    JAVA: """import java.io.*;
import java.util.*;

public class Main {
    public static void main(String[] args) throws IOException {
        BufferedReader in = new BufferedReader(new InputStreamReader(System.in));
        StringTokenizer head = new StringTokenizer(in.readLine());
        int n = Integer.parseInt(head.nextToken());
        long window = Long.parseLong(head.nextToken());
        Map<String, Long> last = new HashMap<>();
        int sent = 0;
        for (int i = 0; i < n; i++) {
            StringTokenizer row = new StringTokenizer(in.readLine());
            long now = Long.parseLong(row.nextToken());
            String key = row.nextToken();
            Long previous = last.get(key);
            if (previous == null || now - previous >= window) {
                sent++;
            }
            last.put(key, now);
        }
        System.out.println(sent);
    }
}
""",
    CPP: """#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    long long window;
    cin >> n >> window;
    unordered_map<string, long long> last;
    int sent = 0;
    for (int i = 0; i < n; i++) {
        long long now;
        string key;
        cin >> now >> key;
        auto found = last.find(key);
        if (found == last.end() || now - found->second >= window) {
            sent++;
        }
        last[key] = now;
    }
    cout << sent << "\\n";
    return 0;
}
""",
    CSHARP: """using System;
using System.Collections.Generic;

var data = Console.In.ReadToEnd().Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries);
int n = int.Parse(data[0]);
long window = long.Parse(data[1]);
var last = new Dictionary<string, long>();
int sent = 0;
for (int i = 0; i < n; i++)
{
    long now = long.Parse(data[2 + 2 * i]);
    string key = data[3 + 2 * i];
    if (!last.TryGetValue(key, out long previous) || now - previous >= window)
    {
        sent++;
    }
    last[key] = now;
}
Console.WriteLine(sent);
""",
    GO: """package main

import (
	"bufio"
	"fmt"
	"os"
)

func main() {
	in := bufio.NewReader(os.Stdin)
	var n int
	var window int64
	fmt.Fscan(in, &n, &window)
	last := map[string]int64{}
	sent := 0
	for i := 0; i < n; i++ {
		var now int64
		var key string
		fmt.Fscan(in, &now, &key)
		previous, seen := last[key]
		if !seen || now-previous >= window {
			sent++
		}
		last[key] = now
	}
	fmt.Println(sent)
}
""",
}

CHEAPEST_ROUTE = {
    JAVA: """import java.io.*;
import java.util.*;

public class Main {
    public static void main(String[] args) throws IOException {
        StreamTokenizer in = new StreamTokenizer(new BufferedReader(new InputStreamReader(System.in)));
        in.nextToken();
        int tests = (int) in.nval;
        StringBuilder out = new StringBuilder();
        for (int test = 0; test < tests; test++) {
            in.nextToken();
            int n = (int) in.nval;
            in.nextToken();
            int m = (int) in.nval;
            List<List<int[]>> graph = new ArrayList<>();
            for (int i = 0; i <= n; i++) graph.add(new ArrayList<>());
            for (int i = 0; i < m; i++) {
                in.nextToken();
                int from = (int) in.nval;
                in.nextToken();
                int to = (int) in.nval;
                in.nextToken();
                int price = (int) in.nval;
                graph.get(from).add(new int[] {to, price});
            }
            long[] best = new long[n + 1];
            Arrays.fill(best, -1);
            best[1] = 0;
            PriorityQueue<long[]> heap = new PriorityQueue<>((a, b) -> Long.compare(a[0], b[0]));
            heap.add(new long[] {0, 1});
            while (!heap.isEmpty()) {
                long[] top = heap.poll();
                long cost = top[0];
                int node = (int) top[1];
                for (int[] edge : graph.get(node)) {
                    if (best[edge[0]] == -1) {
                        best[edge[0]] = cost + edge[1];
                        heap.add(new long[] {best[edge[0]], edge[0]});
                    }
                }
            }
            out.append(best[n]).append('\\n');
        }
        System.out.print(out);
    }
}
""",
    CPP: """#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int tests;
    cin >> tests;
    while (tests--) {
        int n, m;
        cin >> n >> m;
        vector<vector<pair<int, int>>> graph(n + 1);
        for (int i = 0; i < m; i++) {
            int from, to, price;
            cin >> from >> to >> price;
            graph[from].push_back({to, price});
        }
        vector<long long> best(n + 1, -1);
        best[1] = 0;
        priority_queue<pair<long long, int>, vector<pair<long long, int>>, greater<>> heap;
        heap.push({0, 1});
        while (!heap.empty()) {
            auto [cost, node] = heap.top();
            heap.pop();
            for (auto [target, price] : graph[node]) {
                if (best[target] == -1) {
                    best[target] = cost + price;
                    heap.push({best[target], target});
                }
            }
        }
        cout << best[n] << "\\n";
    }
    return 0;
}
""",
    CSHARP: """using System;
using System.Collections.Generic;
using System.Text;

var data = Console.In.ReadToEnd().Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries);
int pos = 0;
int tests = int.Parse(data[pos++]);
var output = new StringBuilder();
for (int test = 0; test < tests; test++)
{
    int n = int.Parse(data[pos++]);
    int m = int.Parse(data[pos++]);
    var graph = new List<(int Target, int Price)>[n + 1];
    for (int i = 0; i <= n; i++) graph[i] = new List<(int Target, int Price)>();
    for (int i = 0; i < m; i++)
    {
        int from = int.Parse(data[pos++]);
        int to = int.Parse(data[pos++]);
        int price = int.Parse(data[pos++]);
        graph[from].Add((to, price));
    }
    var best = new long[n + 1];
    Array.Fill(best, -1L);
    best[1] = 0;
    var heap = new PriorityQueue<(long Cost, int Node), long>();
    heap.Enqueue((0, 1), 0);
    while (heap.Count > 0)
    {
        var (cost, node) = heap.Dequeue();
        foreach (var (target, price) in graph[node])
        {
            if (best[target] == -1)
            {
                best[target] = cost + price;
                heap.Enqueue((best[target], target), best[target]);
            }
        }
    }
    output.Append(best[n]).Append('\\n');
}
Console.Write(output);
""",
    GO: """package main

import (
	"bufio"
	"container/heap"
	"fmt"
	"os"
)

type item struct {
	cost int64
	node int
}

type queue []item

func (q queue) Len() int            { return len(q) }
func (q queue) Less(i, j int) bool  { return q[i].cost < q[j].cost }
func (q queue) Swap(i, j int)       { q[i], q[j] = q[j], q[i] }
func (q *queue) Push(x interface{}) { *q = append(*q, x.(item)) }
func (q *queue) Pop() interface{} {
	old := *q
	last := old[len(old)-1]
	*q = old[:len(old)-1]
	return last
}

type edge struct {
	target int
	price  int64
}

func main() {
	in := bufio.NewReader(os.Stdin)
	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()
	var tests int
	fmt.Fscan(in, &tests)
	for ; tests > 0; tests-- {
		var n, m int
		fmt.Fscan(in, &n, &m)
		graph := make([][]edge, n+1)
		for i := 0; i < m; i++ {
			var from, to int
			var price int64
			fmt.Fscan(in, &from, &to, &price)
			graph[from] = append(graph[from], edge{to, price})
		}
		best := make([]int64, n+1)
		for i := range best {
			best[i] = -1
		}
		best[1] = 0
		pending := &queue{{0, 1}}
		for pending.Len() > 0 {
			top := heap.Pop(pending).(item)
			for _, e := range graph[top.node] {
				if best[e.target] == -1 {
					best[e.target] = top.cost + e.price
					heap.Push(pending, item{best[e.target], e.target})
				}
			}
		}
		fmt.Fprintln(out, best[n])
	}
}
""",
}

CARGO = {
    JAVA: """import java.io.*;
import java.util.*;

public class Main {
    public static void main(String[] args) throws IOException {
        StreamTokenizer in = new StreamTokenizer(new BufferedReader(new InputStreamReader(System.in)));
        in.nextToken();
        int n = (int) in.nval;
        in.nextToken();
        int capacity = (int) in.nval;
        long[] best = new long[capacity + 1];
        for (int i = 0; i < n; i++) {
            in.nextToken();
            int weight = (int) in.nval;
            in.nextToken();
            int value = (int) in.nval;
            for (int load = weight; load <= capacity; load++) {
                best[load] = Math.max(best[load], best[load - weight] + value);
            }
        }
        System.out.println(best[capacity]);
    }
}
""",
    CPP: """#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, capacity;
    cin >> n >> capacity;
    vector<long long> best(capacity + 1, 0);
    for (int i = 0; i < n; i++) {
        int weight, value;
        cin >> weight >> value;
        for (int load = weight; load <= capacity; load++) {
            best[load] = max(best[load], best[load - weight] + value);
        }
    }
    cout << best[capacity] << "\\n";
    return 0;
}
""",
    CSHARP: """using System;

var data = Console.In.ReadToEnd().Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries);
int n = int.Parse(data[0]);
int capacity = int.Parse(data[1]);
var best = new long[capacity + 1];
for (int i = 0; i < n; i++)
{
    int weight = int.Parse(data[2 + 2 * i]);
    int value = int.Parse(data[3 + 2 * i]);
    for (int load = weight; load <= capacity; load++)
    {
        best[load] = Math.Max(best[load], best[load - weight] + value);
    }
}
Console.WriteLine(best[capacity]);
""",
    GO: """package main

import (
	"bufio"
	"fmt"
	"os"
)

func main() {
	in := bufio.NewReader(os.Stdin)
	var n, capacity int
	fmt.Fscan(in, &n, &capacity)
	best := make([]int64, capacity+1)
	for i := 0; i < n; i++ {
		var weight int
		var value int64
		fmt.Fscan(in, &weight, &value)
		for load := weight; load <= capacity; load++ {
			if candidate := best[load-weight] + value; candidate > best[load] {
				best[load] = candidate
			}
		}
	}
	fmt.Println(best[capacity])
}
""",
}

PHP = "php-8.5"
PHP_INPUT = "$data = preg_split('/\\s+/', trim(stream_get_contents(STDIN)));\n"

COUNT_BELOW[PHP] = (
    """<?php
function countBelow(array $values, int $x): int {
    $lo = 0;
    $hi = count($values) - 1;
    while ($lo < $hi) {
        $mid = intdiv($lo + $hi, 2);
        if ($values[$mid] < $x) {
            $lo = $mid + 1;
        } else {
            $hi = $mid;
        }
    }
    return $lo;
}

"""
    + PHP_INPUT
    + """$n = (int) $data[0];
$values = array_map('intval', array_slice($data, 1, $n));
$q = (int) $data[1 + $n];
$total = 0;
for ($i = 0; $i < $q; $i++) {
    $total += countBelow($values, (int) $data[2 + $n + $i]);
}
echo $total, "\\n";
"""
)

ALERT_REPEATS[PHP] = (
    "<?php\n"
    + PHP_INPUT
    + """$n = (int) $data[0];
$window = (int) $data[1];
$last = [];
$sent = 0;
for ($i = 0; $i < $n; $i++) {
    $now = (int) $data[2 + 2 * $i];
    $key = $data[3 + 2 * $i];
    if (!isset($last[$key]) || $now - $last[$key] >= $window) {
        $sent++;
    }
    $last[$key] = $now;
}
echo $sent, "\\n";
"""
)

CHEAPEST_ROUTE[PHP] = (
    "<?php\n"
    + PHP_INPUT
    + """$pos = 0;
$tests = (int) $data[$pos++];
$answers = [];
for ($test = 0; $test < $tests; $test++) {
    $n = (int) $data[$pos++];
    $m = (int) $data[$pos++];
    $graph = array_fill(0, $n + 1, []);
    for ($i = 0; $i < $m; $i++) {
        $from = (int) $data[$pos++];
        $to = (int) $data[$pos++];
        $price = (int) $data[$pos++];
        $graph[$from][] = [$to, $price];
    }
    $best = array_fill(0, $n + 1, -1);
    $best[1] = 0;
    $heap = new SplMinHeap();
    $heap->insert([0, 1]);
    while (!$heap->isEmpty()) {
        [$cost, $node] = $heap->extract();
        foreach ($graph[$node] as [$target, $price]) {
            if ($best[$target] === -1) {
                $best[$target] = $cost + $price;
                $heap->insert([$best[$target], $target]);
            }
        }
    }
    $answers[] = $best[$n];
}
echo implode("\\n", $answers), "\\n";
"""
)

CARGO[PHP] = (
    "<?php\n"
    + PHP_INPUT
    + """$n = (int) $data[0];
$capacity = (int) $data[1];
$best = array_fill(0, $capacity + 1, 0);
for ($i = 0; $i < $n; $i++) {
    $weight = (int) $data[2 + 2 * $i];
    $value = (int) $data[3 + 2 * $i];
    for ($load = $weight; $load <= $capacity; $load++) {
        $best[$load] = max($best[$load], $best[$load - $weight] + $value);
    }
}
echo $best[$capacity], "\\n";
"""
)

STARTERS = {
    "count-below": COUNT_BELOW,
    "alert-repeats": ALERT_REPEATS,
    "cheapest-route": CHEAPEST_ROUTE,
    "cargo-value": CARGO,
}
