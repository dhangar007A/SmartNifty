#pragma once
#include <iostream>
#include <vector>
#include <string>
#include <map>
#include <fstream>
#include <sstream>
#include <cmath>
#include <thread>
#include <mutex>
#include <deque>
#include <functional>
#include <chrono>
#include <iomanip>

using namespace std;

struct OptionChainFormat{
    double ltp1, change1, volume1, oi1;
    double ltp2, change2, volume2, oi2;
    int strike;
};

class StrikeToTokenMapper{
private:
    map<pair<int, string>, int> M;

public:
    int m_50_token {};
    int m_UT_token {};

    StrikeToTokenMapper(string path, string OptionExpiry, string FutureExpiry);
    
    int getToken(int strike, const string& option) const;
};

class OptionChainCreater : public StrikeToTokenMapper{
private:
    int m_UR, m_LR;
    mutable mutex mtx;
    
    vector<OptionChainFormat> m_OC; // OC -> OptionChain
    vector<double> m_SF; // SF -> SpotFuture
    long long m_ET; // ET -> ExchangeTimestamp

public:
    OptionChainCreater(int UR, int LR, string path, string OptionExpiry, string FutureExpiry);

    vector<double> getLTP(string path);
    
    string getTimestamp(long long unix_time);
    
    void readTokenData(string path, int strike_diff);
    
    vector<OptionChainFormat> getOptionChain();

    vector<double> getSpotFuture();

    long long getExcahngeTimestamp();
    
    friend class TablePlotter;
};
