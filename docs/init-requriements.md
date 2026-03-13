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


