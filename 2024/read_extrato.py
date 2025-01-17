#%%
import pandas as pd

extrato = pd.read_excel(r"2024\extratopif2024.xlsx")

#%%

nomes = extrato.transf

def arruma_nome(x:str):
    nome = x[10:-5].strip().lower()
    if nome == '55.257.':
        nome = 'pedro r'
    return nome.capitalize()

nomes = nomes.apply(arruma_nome)

#%%

extrato.transf = nomes

#%%

extrato