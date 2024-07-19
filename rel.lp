\ Model _copy
\ LP format - for model browsing. Use MPS format to capture full model detail.
Minimize
  2 output[thermal1,0600] + 2 output[thermal1,0700]
   + 2 output[thermal1,0800] + 2 output[thermal1,0900]
   + 2 output[thermal1,1000] + 1.3 output[thermal2,0600]
   + 1.3 output[thermal2,0700] + 1.3 output[thermal2,0800]
   + 1.3 output[thermal2,0900] + 1.3 output[thermal2,1000]
   + 3 output[thermal3,0600] + 3 output[thermal3,0700]
   + 3 output[thermal3,0800] + 3 output[thermal3,0900]
   + 3 output[thermal3,1000] - 700 num_active[thermal1,0600]
   - 700 num_active[thermal1,0700] - 700 num_active[thermal1,0800]
   - 700 num_active[thermal1,0900] - 700 num_active[thermal1,1000]
   + 975 num_active[thermal2,0600] + 975 num_active[thermal2,0700]
   + 975 num_active[thermal2,0800] + 975 num_active[thermal2,0900]
   + 975 num_active[thermal2,1000] - 1500 num_active[thermal3,0600]
   - 1500 num_active[thermal3,0700] - 1500 num_active[thermal3,0800]
   - 1500 num_active[thermal3,0900] - 1500 num_active[thermal3,1000]
   + 2000 num_startup[thermal1,0600] + 2000 num_startup[thermal1,0700]
   + 2000 num_startup[thermal1,0800] + 2000 num_startup[thermal1,0900]
   + 2000 num_startup[thermal1,1000] + 1000 num_startup[thermal2,0600]
   + 1000 num_startup[thermal2,0700] + 1000 num_startup[thermal2,0800]
   + 1000 num_startup[thermal2,0900] + 1000 num_startup[thermal2,1000]
   + 500 num_startup[thermal3,0600] + 500 num_startup[thermal3,0700]
   + 500 num_startup[thermal3,0800] + 500 num_startup[thermal3,0900]
   + 500 num_startup[thermal3,1000]
Subject To
 R0: output[thermal1,0600] + output[thermal2,0600] + output[thermal3,0600]
   = 15000
 R1: output[thermal1,0700] + output[thermal2,0700] + output[thermal3,0700]
   = 30000
 R2: output[thermal1,0800] + output[thermal2,0800] + output[thermal3,0800]
   = 25000
 R3: output[thermal1,0900] + output[thermal2,0900] + output[thermal3,0900]
   = 40000
 R4: output[thermal1,1000] + output[thermal2,1000] + output[thermal3,1000]
   = 27000
 R5: output[thermal1,0600] - 850 num_active[thermal1,0600] >= 0
 R6: output[thermal1,0700] - 850 num_active[thermal1,0700] >= 0
 R7: output[thermal1,0800] - 850 num_active[thermal1,0800] >= 0
 R8: output[thermal1,0900] - 850 num_active[thermal1,0900] >= 0
 R9: output[thermal1,1000] - 850 num_active[thermal1,1000] >= 0
 R10: output[thermal2,0600] - 1250 num_active[thermal2,0600] >= 0
 R11: output[thermal2,0700] - 1250 num_active[thermal2,0700] >= 0
 R12: output[thermal2,0800] - 1250 num_active[thermal2,0800] >= 0
 R13: output[thermal2,0900] - 1250 num_active[thermal2,0900] >= 0
 R14: output[thermal2,1000] - 1250 num_active[thermal2,1000] >= 0
 R15: output[thermal3,0600] - 1500 num_active[thermal3,0600] >= 0
 R16: output[thermal3,0700] - 1500 num_active[thermal3,0700] >= 0
 R17: output[thermal3,0800] - 1500 num_active[thermal3,0800] >= 0
 R18: output[thermal3,0900] - 1500 num_active[thermal3,0900] >= 0
 R19: output[thermal3,1000] - 1500 num_active[thermal3,1000] >= 0
 R20: output[thermal1,0600] - 2000 num_active[thermal1,0600] <= 0
 R21: output[thermal1,0700] - 2000 num_active[thermal1,0700] <= 0
 R22: output[thermal1,0800] - 2000 num_active[thermal1,0800] <= 0
 R23: output[thermal1,0900] - 2000 num_active[thermal1,0900] <= 0
 R24: output[thermal1,1000] - 2000 num_active[thermal1,1000] <= 0
 R25: output[thermal2,0600] - 1750 num_active[thermal2,0600] <= 0
 R26: output[thermal2,0700] - 1750 num_active[thermal2,0700] <= 0
 R27: output[thermal2,0800] - 1750 num_active[thermal2,0800] <= 0
 R28: output[thermal2,0900] - 1750 num_active[thermal2,0900] <= 0
 R29: output[thermal2,1000] - 1750 num_active[thermal2,1000] <= 0
 R30: output[thermal3,0600] - 4000 num_active[thermal3,0600] <= 0
 R31: output[thermal3,0700] - 4000 num_active[thermal3,0700] <= 0
 R32: output[thermal3,0800] - 4000 num_active[thermal3,0800] <= 0
 R33: output[thermal3,0900] - 4000 num_active[thermal3,0900] <= 0
 R34: output[thermal3,1000] - 4000 num_active[thermal3,1000] <= 0
 R35: 2000 num_active[thermal1,0600] + 1750 num_active[thermal2,0600]
   + 4000 num_active[thermal3,0600] >= 17250
 R36: 2000 num_active[thermal1,0700] + 1750 num_active[thermal2,0700]
   + 4000 num_active[thermal3,0700] >= 34500
 R37: 2000 num_active[thermal1,0800] + 1750 num_active[thermal2,0800]
   + 4000 num_active[thermal3,0800] >= 28750
 R38: 2000 num_active[thermal1,0900] + 1750 num_active[thermal2,0900]
   + 4000 num_active[thermal3,0900] >= 46000
 R39: 2000 num_active[thermal1,1000] + 1750 num_active[thermal2,1000]
   + 4000 num_active[thermal3,1000] >= 31050
 startup[thermal1,2024_07_19T07_00_00]: num_active[thermal1,0600]
   - num_active[thermal1,0700] + num_startup[thermal1,0700] >= 0
 startup[thermal1,2024_07_19T08_00_00]: num_active[thermal1,0700]
   - num_active[thermal1,0800] + num_startup[thermal1,0800] >= 0
 startup[thermal1,2024_07_19T09_00_00]: num_active[thermal1,0800]
   - num_active[thermal1,0900] + num_startup[thermal1,0900] >= 0
 startup[thermal1,2024_07_19T10_00_00]: num_active[thermal1,0900]
   - num_active[thermal1,1000] + num_startup[thermal1,1000] >= 0
 startup[thermal2,2024_07_19T07_00_00]: num_active[thermal2,0600]
   - num_active[thermal2,0700] + num_startup[thermal2,0700] >= 0
 startup[thermal2,2024_07_19T08_00_00]: num_active[thermal2,0700]
   - num_active[thermal2,0800] + num_startup[thermal2,0800] >= 0
 startup[thermal2,2024_07_19T09_00_00]: num_active[thermal2,0800]
   - num_active[thermal2,0900] + num_startup[thermal2,0900] >= 0
 startup[thermal2,2024_07_19T10_00_00]: num_active[thermal2,0900]
   - num_active[thermal2,1000] + num_startup[thermal2,1000] >= 0
 startup[thermal3,2024_07_19T07_00_00]: num_active[thermal3,0600]
   - num_active[thermal3,0700] + num_startup[thermal3,0700] >= 0
 startup[thermal3,2024_07_19T08_00_00]: num_active[thermal3,0700]
   - num_active[thermal3,0800] + num_startup[thermal3,0800] >= 0
 startup[thermal3,2024_07_19T09_00_00]: num_active[thermal3,0800]
   - num_active[thermal3,0900] + num_startup[thermal3,0900] >= 0
 startup[thermal3,2024_07_19T10_00_00]: num_active[thermal3,0900]
   - num_active[thermal3,1000] + num_startup[thermal3,1000] >= 0
 initial_startup[thermal1]: - num_active[thermal1,0600]
   + num_startup[thermal1,0600] >= 0
 initial_startup[thermal2]: - num_active[thermal2,0600]
   + num_startup[thermal2,0600] >= 0
 initial_startup[thermal3]: - num_active[thermal3,0600]
   + num_startup[thermal3,0600] >= 0
Bounds
 num_active[thermal1,0600] <= 12
 num_active[thermal1,0700] <= 12
 num_active[thermal1,0800] <= 12
 num_active[thermal1,0900] <= 12
 num_active[thermal1,1000] <= 12
 num_active[thermal2,0600] <= 10
 num_active[thermal2,0700] <= 10
 num_active[thermal2,0800] <= 10
 num_active[thermal2,0900] <= 10
 num_active[thermal2,1000] <= 10
 num_active[thermal3,0600] <= 5
 num_active[thermal3,0700] <= 5
 num_active[thermal3,0800] <= 5
 num_active[thermal3,0900] <= 5
 num_active[thermal3,1000] <= 5
End
