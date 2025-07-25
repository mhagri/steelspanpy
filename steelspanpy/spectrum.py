import numpy as np

def Sae(name, sds, sd1, r, d, i, Tmax=5.0, dt=5):
    period = np.arange(0, Tmax+dt, dt)
    T_B = sd1 / sds
    T_A = 0.2 * T_B
    T_L = 6.0
    valuesSae = []
    for T in period:

        if 0 <= T <= T_A:
            Sae = ((0.4 + 0.6 * (T / T_A)) * sds) / (d + (r / i - d) * T / T_B)
        elif T_A < T <= T_B:
            Sae = sds / (d + (r / i - d) * T / T_B)
        elif T_B < T <= T_L:
            Sae = (sd1 / T) / (r / i)
        else:
            Sae = (sd1 * (T_L / pow(T, 2))) / (r / i)
        valuesSae.extend((name,str(T),str(Sae)))
        
    valuesSae = [sep.replace('.', ',') for sep in valuesSae]
        
    return valuesSae


def Saed(name, sds, sd1, dt=0.01):
    T_B = (sd1 / sds) / 3
    T_A = (0.2 * T_B) / 3
    T_L = 3.0
    period = np.arange(0, T_L, dt)
    valuesSaed = []
    for T in period:
        if 0 <= T <= T_A:
            Saed = ((0.32 + 0.48 * (T / T_A)) * sds)
        elif T_A < T <= T_B:
            Saed = 0.8 * sds
        else:
            Saed = (0.8 * sds * T_B) / T
        valuesSaed.extend((name,str(T),str(Saed)))
        
    valuesSaed = [sep.replace('.', ',') for sep in valuesSaed]
        
    return valuesSaed

