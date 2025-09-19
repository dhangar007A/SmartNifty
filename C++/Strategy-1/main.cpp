#include "../include/OptionChainCreater.hpp"
#include "../include/TablePlotter.hpp"

#include <iostream>
#include <thread>
#include <chrono>

using namespace std;

map<string, string> TXTReader(const string& path){
    ifstream Parameters(path);

    map<string, string> P;
    if(!Parameters.is_open()){
        cerr << "Error opening Parameters file: " << path << endl;
        return P; 
    }

    string line;
    while(getline(Parameters, line)){
        if(line.empty() || line[0] == '#') 
            continue;

        size_t pos = line.find('=');
        if(pos != string::npos){
            string key = line.substr(0, pos);
            string value = line.substr(pos + 1);

            P[key] = value;
        }
    }

    Parameters.close(); 
    return P;
}

int main(){
    map<string, string> P = TXTReader("../Strategy-1/Parameters.txt");
    
    int UpperRange = stoi(P["UpperRange"]);
    int LowerRange = stoi(P["LowerRange"]);
    int StrikeDiff = stoi(P["StrikeDiff"]);

    OptionChainCreater OCC(UpperRange, LowerRange, "../../Ticker.csv", P["OptionExpiry"], P["FutureExpiry"]);

    thread t1(&OptionChainCreater::readTokenData, &OCC, "../../tickers/", StrikeDiff);
    this_thread::sleep_for(chrono::milliseconds(1000));
    
    TablePlotter TP;
    
    for(int i = 0; ; i++){
        vector<double> SF = OCC.getSpotFuture();
        vector<OptionChainFormat> OC = OCC.getOptionChain();
        
        TP.displaySpotFuture(SF);
        TP.displayOptionChain(OC);

        this_thread::sleep_for(chrono::milliseconds(1000));
    }

    t1.join();
    return 0;
}