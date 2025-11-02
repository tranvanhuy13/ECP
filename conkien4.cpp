#include <bits/stdc++.h>
using namespace std;

const long long MOD = 1e9 + 7;

long long ck(int m, int n) {
    vector<long long> a(n + 1, 1);
    for (int i = 1; i <= m; i++) {
        for (int j = 1; j <= n; j++) {
            a[j] = (a[j] + a[j - 1]) % MOD;
        }
    }
    return a[n];
}

int main() {
    int m, n;
    cin >> m >> n;
    cout << ck(m, n);
    return 0;
}

