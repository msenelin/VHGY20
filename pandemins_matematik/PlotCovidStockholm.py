import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint
from numpy import exp
from pylab import rcParams

''' Textfilen StockholmCovid.csv innehåller antalet nya rapporterade fall i
    Stockholm per dag. Från detta skapar vi en lista som innehåller de totala
    antalet fall varje dag. Se till så att du har laddat ner denna fil.

    Det totala antalet fall varje dag, är det totala antalet fall från föregående
    dag + nya fall. Denna lista skapar vi enligt nedan.

    VIKTIGT: notera att vi även här (precis som i PlotCovid2.py) har ett stort
    mörkertal. Datan vi har är enbart de rapporterade fallen. De som har haft
    Covid med inte testat sig finns inte med i datan.
'''

#se till så att du har filen StockholmCovid.csv nedladdad i samma mapp som du har denna fil i
df = pd.read_csv('StockholmCovid.csv', parse_dates=['date']) #läser in data

#fixa till stockholmsdatan...
sthlm_data = []
prev_total = 0
for index, row in df.iterrows():
    curr_total = prev_total + row['new_cases'] #totala antalet fall idag = totala antalet fall igår + antal nya fall idag
    sthlm_data.append(curr_total)
    prev_total = curr_total

df['total_cases'] = sthlm_data #... och spara denna 'nya' data i vår data frame
#print(df)


''' Vår SIR-model där vi kan applya restriktioner, lik filen SIR_restrictions.py.
    Notera: nu räknar modellen ut ANTAL (S, I, R), istället för ANDEL (s, i r)
'''
def model(z,t, b, restrictionsApplied, daysOfRestriction, startDay, b0, b_min): #ta in b som parameter!
    S = z[0]
    I = z[1]
    R = z[2]
    k = 0.125 #=1/8 k=1/D där D är antal dagar en person är infekterad i snitt
    #kom ihåg: R_0 = b/k
    ''' Om restrictionsApplied=True så kommer datorn gå in i allt som står
        i blocket nedan (allt som är indenerat/tabat under if-satsen)
    '''
    if restrictionsApplied:
        #~~~början på block~~
        n=0.1 #en förändringsfaktor, sätt inte ett större värde än 1!
        if t>startDay and t<startDay+daysOfRestriction:
            #****början på block****
            ''' Om den nuvararande tidpunkten/dagen befinner sig i intervallet då
                vi har restriktioner, så ges b av formeln nedan. Denna formeln
                gör så att inte b går direkt från b0 till b_min, utan att det
                blir en 'mjuk' övergång från b0 till b_min. Om vi istället
                sätter b=b_min så kommer vi få ett 'hack' i kurvan. Testa själv!
                Du väljer själv om du vill ha en direkt övergång eller en gradvis övergång.
            '''
            t1 = t - startDay #för att få 'rätt' t till formeln nedan
            b= b0* exp(- n * t1) + (1 - exp(- n * t1)) * b_min #b kommer gå mjukt från b0 till b_min
            #****slut på block****
        if t>=startDay+daysOfRestriction:
            #^^^^början på block^^^
            ''' När restriktionerna är slut så kommer b gå från b_min tillbaka
                till b_0 med en 'mjuk' övergång. Ju större n är, desto snabbare
                sker övergången!
            '''
            t2 = t - startDay - daysOfRestriction
            b= b_min* exp(- n * t2) + (1 - exp(- n * t2)) * b0 #b kommer gå mjukt från b_min till b0
            #^^^^slut på block^^^^
        #~~~~slut på block~~~~
    dSdt = -b*S*I/N
    dIdt = b*S*I/N-k*I
    dRdt = k*I
    dzdt = [dSdt,dIdt, dRdt]
    return dzdt

#NOTERA: i FHMs data - vad räknas som Stockholm? Kolla upp det och sätt det som värdet på N!
#N = 230000 #Stockholms LÄNs invånarantal
N = 974000 #befolkning i Stockholm enligt https://start.stockholm/om-stockholms-stad/utredningar-statistik-och-fakta/statistik/befolkning/
#begynnelsevillkor, S(0)=N-1, I(0)=q, R(0)
z0 = [N-1,1,0]

#antal tidpunkter (dagar) vi vill lösa differentialakvationen för
number_of_days = len(df.index) #så många dagar vi har covid-19 data för

#skapar en lista med tidpunkterna [0, 1, 2, 3, ..., number_of_days-1]
t = np.linspace(0,number_of_days-1,number_of_days)

#löser SIR-modellen
b1 = 0.31 #=0.125 #b=R0*k R≈2.5, k≈1/8=0.125 ==> b≈2.5*0.125≈0.31
b_min = 0.07
solution1 = odeint(model, z0, t, args=(b1, True, 150, 60, b1, b_min)) #med restriktioner
solution2 = odeint(model, z0, t, args=(b1, False, 150, 60, b1, b_min)) #utan restriktioner
''' solution innehåller lösningarna till alla tre: S(t), I(t) & R(t). solution
    är en lista av längd n=365. Varje element i denna lista ger lösningen av
    differentialekvationerna vid varje tidpunkt. Vart och ett av dessa element
    är i sin tur en lista av längd 3, på formen [S(t_j), I(t_j), R(t_j)] där
    t_j är en specifik tidpunkt (exempelvis dag 73). Alltså;
    solution = [[S(0), I(0), R(0)], [S(1), I(1), R(1)], ... ]
'''
#lösning 1
solution1_r = solution1[:, 2]
solution1_i = solution1[:, 1]
solution1_r_plus_i = solution1_r + solution1_i
df['theoretical_cases1'] = solution1_r_plus_i
#print(ri_solution1)

#lösning 2
solution2_r = solution2[:, 2]
solution2_i = solution2[:, 1]
solution2_r_plus_i = solution2_r + solution2_i
df['theoretical_cases2'] = solution2_r_plus_i
#print(ri_solution2)

print(df)

ax = plt.gca()
df.plot(kind='line', x='date', y='theoretical_cases1', ax=ax, color='orange', label = 'Teoretiskt antal fall, scenario 1')
df.plot(kind='line', x='date', y='theoretical_cases2', ax=ax, color='purple', label = 'Teoretiskt antal fall, scenario 2')
df.plot(kind='line', x='date', y='total_cases', ax=ax, color='pink', figsize=(10,7), label="Totalt antal rapporterade fall")

plt.legend(loc='best') #väljer den 'bästa' platsen för linjebeskrivningarna
plt.ylabel("Antal")
plt.xlabel("Dag")
plt.ylim(bottom=0) #låt y-axeln börja på noll
#plt.savefig("StockholmCovidRealAndTheoretical.png")
plt.show()
