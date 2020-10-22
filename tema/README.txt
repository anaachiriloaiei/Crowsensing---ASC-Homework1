Tema 1 ASC - Crowdsensing
Achiriloaiei Ana
334 CC


Pentru implemetarea temei, eu am considerat necesare:
        1)O bariera rentrant - pentru a sincroniza threadurile master. 
        Acestea sunt cele care deschid 8 threaduri si asteapta
        ca ele sa se termine. Din cauza faptului ca unele threaduri master se vor
        termina mai repede decat altele, este necesara existenta unei bariere
        pentru a nu lasa un thread master sa treaca la urmatorul timepoint pana
        cand toate threadurile master ajung la bariera.
        2)O dictionar-voi adauga perechi de genul (locatie, lock). Un loc al unei
        locatii va restrictiona accesul unui singur thread, la locatia respectiva.
        Adica un singur thread poate citi/scrie la un moment dat.
        3)O coada - in care se vor afla tupluri de forma (script, location, neighbours)
        care vor fi luate pe rand de threadurile worker si prelucrate.
        
Fiecare device, primeste o bariera rentranta comuna si lock-uri comune pentru
fiecare locatie.Device-ul cu id egal cu 0 este cel care creaza bariera si lock-urile
si le transmite mai departe tuturor deviceurilor in setup_device().Fiecare device 
va avea un thread master, care dupa distribuirea lock-urilor si a barierei va fi
pornit pentru fiecare device.
DeviceThread - aici se afla treadul master al fiecarui device.Mai intai pornesc 8
threaduri worker.Pentru fiecare timepoint se vor realiza mai multe operatii: se
afla vecinii, se asteapta primirea tututor scripturilor, se adauga in coada tuplurile,
se asteapta prelucrarea tuturor scripturilor, dupa care se va intra in bariera pentru
a astepta toate threadurile master sa ajunga acolo pentru a se putea trece la urmatorul
timepoint.
MyThread - threadurile care ruleaza scriptul. Initial, este acaparat lock-ul pentru
locatia primita, colecteaza date de la vecini pentru locatie si datele proprii, 
ruleaza script-ul pe datele colectate, actualizeaza datele vecinilor si cele 
proprii pentru locatie, iar in final se elibereaza lock-ul pentru locatia primita,
pentru a lasa si alti workeri sa aiba access la locatia respectiva.

