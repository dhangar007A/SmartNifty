#pragma once

#include "OptionChainCreater.hpp"
#include <tabulate/table.hpp>

using namespace tabulate;

class TablePlotter{
public:
    string toString(double x);

    void prepareOptionChainTable(vector<OptionChainFormat>& v);
    
    void displayOptionChain(OptionChainCreater& f);
    void displayOptionChain(vector<OptionChainFormat>& v);

    void prepareSpotFutureTable(vector<double>& v);
    
    void displaySpotFuture(OptionChainCreater& f);
    void displaySpotFuture(vector<double>& v);
};
