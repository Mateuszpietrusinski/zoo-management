# Role

Wciel się w rolę product managera który będzie moim asystentem przy planowaniu projektu.

# context

Jestem na bardzo wstępnym etapie planowania projektu Mam podstawowe temat oraz kilka wymagań technicznych które chciałbym spełnić ale na pewno chciałbym uszczegółowić wiele z tych zagadnień Chciałbym wykonać wyznaczyć kilka ficzerów które są związane też z procesami biznesowymi które zachodzą w tej domenie Może zaczniemy od procesu biznesowych które chodzą w tej domenie i spróbowaniu sobie ich zmapować chciałbym użyć tego diagramów BPMN aby pokazać te procesy on powinien być zapisane w pliku BPNM który łatwo potem otworzyć na BPMN.io.

#context techniczny
Wymagania w skrócie

● Minimum 8 klas z pełną hierarchią

● Wszystkie 4 filary OOP (abstrakcja, enkapsulacja, dziedziczenie, polimorfizm)

● Co najmniej 3 typy relacji (asocjacja, agregacja, kompozycja)

● Klasy abstrakcyjne (ABC) i @property

● Metody specjalne (__repr__, __str__, __eq__)

● Minimum 10 testów jednostkowych (pytest) ~ integracyjnych

- Scenariusze BDD do procesow biznesowych BPMN oraz testy bdd

● Dokumentacja (docstrings)

● Prosty diagram klas i kilka User Stories w README - nie musicie być ekspertami od

UML ani Agile, chodzi o to żebyście przemyśleli projekt przed kodowaniem



Sugerowane klasy:

Animal (ABC) → Mammal → Lion, Elephant, Monkey

→ Bird → Eagle, Penguin

→ Reptile → Crocodile

Enclosure, Zoo

Employee (ABC) → Zookeeper, Veterinarian, Guide

FeedingSchedule

Relacje:



- Zoo ◆── Enclosure (kompozycja)

- Enclosure ◇── Animal (agregacja)

- Zookeeper ── Enclosure (asocjacja)

- Zoo ◇── Employee (agregacja)







# task

Twoje zadanie to zaplanowac plan listy procesow zachodzacych w tej domenie uwzgedniajac wymagania techniczne. Projekt nie pownien byc zbyt duzy aby nie powodowal problemow przy ocenie