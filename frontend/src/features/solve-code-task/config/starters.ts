/** A minimal program that reads all of stdin, so nobody spends test time on input plumbing. */
const STARTERS: Record<string, string> = {
  'python-3.14': `import sys

data = sys.stdin.read().split()
`,
  'typescript-deno': `const input = await new Response(Deno.stdin.readable).text()
const lines = input.split('\\n')
`,
  'openjdk-25': `import java.io.*;
import java.util.*;

public class Main {
    public static void main(String[] args) throws IOException {
        BufferedReader in = new BufferedReader(new InputStreamReader(System.in));
        int t = Integer.parseInt(in.readLine().trim());
    }
}
`,
  'g++-15': `#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    cin >> t;
    return 0;
}
`,
  'gcc-15': `#include <stdio.h>

int main(void) {
    int t;
    scanf("%d", &t);
    return 0;
}
`,
  'dotnet-csharp-9': `using System;

int t = int.Parse(Console.ReadLine()!);
`,
  'go-1.26': `package main

import (
	"bufio"
	"fmt"
	"os"
)

func main() {
	in := bufio.NewReader(os.Stdin)
	var t int
	fmt.Fscan(in, &t)
}
`,
  'rust-1.93': `use std::io::{self, Read};

fn main() {
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).unwrap();
    let mut tokens = input.split_ascii_whitespace();
}
`,
}

export const starterFor = (language: string) => STARTERS[language] ?? ''
