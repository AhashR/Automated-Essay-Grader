Profile related technical learning story Sprint 2 version 1: De context en doelen
In sprint 2 is het hoofddoel van ons team om de infrastructuur aan te leggen die al onze individuele componenten met elkaar verbindt. Ik ga een website maken met een AI-interface waar je een learning story in kunt gooien om feedback te krijgen. De AI-feedback hoeft nu nog niet perfect te zijn, het belangrijkste is dat de hele keten samenwerkt zodat we later makkelijk een betere AI kunnen inpluggen. Mijn specifieke rol als Cloud engineer is het bouwen van deze website met de interface en, in samenwerking met mijn security teamgenoot, zorgen dat deze applicatie veilig is.
Leerdoel
Ik wil leren hoe ik een functionerende website bouw, deze koppel aan een backend, en deze applicatie vervolgens veilig en gestructureerd uitrol naar de cloud.
Leeruitkomsten
Ik ontwerp, bouw en test cloud-gebaseerde infrastructuur.
Ik pas basis security-principes toe in de configuratie en deployment van een applicatie.
Bewijsstukken
Om mijn leerdoelen aan te tonen, lever ik het volgende op:
De source code: Een link naar onze Gitlab repository met mijn commits voor de website.
Deployment documentatie: Een document met de exacte commandos en configuraties zoals Docker en Terraform die ik heb gebruikt om de website naar de cloud te uploaden.
Diagram: Een visueel schema dat laat zien hoe de frontend, backend en cloud-infrastructuur met elkaar verbonden zijn.
Security checklist: Een kort verslag, afgetekend door mijn security-teamgenoot, waarin we aantonen welke specifieke stappen we hebben gezet om de website te beveiligen zoals input validatie en veilige verbindingen.
Activiteiten en microplanning
Week 1: Ik schrijf de code in Vue voor de chat interface van de website en zorg dat deze lokaal succesvol kan communiceren met de AI-backend van mijn teamgenoten.
Week 2: Ik plan een meeting in met mijn security teamgenoot. Samen implementeren we basisbeveiliging op de website zoals input-sanitization voor het tekstvak en we testen dit door bewust foute data in te voeren.
Week 3: Ik schrijf de benodigde scripts om de website naar Google cloud te pushen. Vervolgens voer ik de deployment uit en documenteer ik het proces en de architectuur in een definitief opleverdocument voor de sprint review.


feedback on version 1: This learning story is too vague and generic. It is not well connected to the project context. You need to talk mention the requirements or at least that you will find out what the requirements are. Also, explain what kind of infrastructure you are after and what kind of application you plan to build.
At the moment this is a no go.

made version based on feedback of version 1 so here version 2: Context en doelen
In sprint 2 is mijn belangrijkste taak om een veilige cloud infrastructuur te ontwerpen voor onze AI feedback applicatie. De grootste technische uitdaging is exact uitzoeken hoe de chat-interface, de Node.js backend en het lokale taalmodel met elkaar communiceren. Ik onderzoek hiervoor verschillende protocollen. Ik vergelijk standaard REST API verbindingen met alternatieven zoals Server-Sent Events voor het direct streamen van tekst en het MCP voor het integreren van AI tools. Uiteindelijk kies ik bewust voor een REST architectuur. Dit zorgt voor een snellere en simpelere deployment op Google cloud run en garandeert een stabielere verbinding, waarbij we de wachttijd voor de gebruiker voor nu accepteren. Ik documenteer deze keuze uitgebreid.

Voor de live-omgeving zet ik de applicatie in Google cloud. Ik gebruik Docker om de applicatie in te pakken in containers. Het grote voordeel hiervan is dat de code overal exact hetzelfde draait, in tegenstelling tot het direct installeren van code op een server wat vaak voor versieproblemen zorgt. Voor het aanmaken van de cloud diensten gebruik ik Terraform als Infrastructure as Code. Het alternatief is alles handmatig aanklikken in de google cloud console, maar met Terraform is de infrastructuur versiebeheerd, herbruikbaar en minder foutgevoelig. Ik kies specifiek voor Google cloud run als hosting in plaats van virtuele machines via Compute Engine. Cloud run is namelijk serverless en schaalt automatisch op, waardoor ik geen heel besturingssysteem hoef te updaten en onderhouden.

Samen met de security engineer beveilig ik de datastromen. We gebruiken bewust geen statische wachtwoorden of lange termijn API sleutels voor de deployment. In plaats daarvan implementeren we Workload Identity Federation en IAM service accounts voor veilige en tijdelijke authenticatie tussen onze GitLab omgeving en Google Cloud.
Goals
1. Analysis: Ik doe diepgaand technisch onderzoek naar communicatieprotocollen en cloud hosting opties, weeg de alternatieven tegen elkaar af en kies de beste oplossing voor onze architectuur.
2. Realise: Ik programmeer de daadwerkelijke infrastructuur via Docker en Terraform en richt de automatische en veilige cloud omgeving in.

# Leerdoel
Ik wil leren hoe ik op een methodische manier communicatieprotocollen tussen een chat-interface en een AI backend onderzoek, en hoe ik deze componenten via Infrastructure as Code en containers schaalbaar en cryptografisch beveiligd uitrol naar Google Cloud.

# Leeruitkomsten
• Ik analyseer en vergelijk netwerkprotocollen zoals REST, Server-Sent Events en MCP om de meest efficiënte communicatie op te zetten tussen de chat-interface en een taalmodel, waarbij ik mijn definitieve keuze voor REST onderbouw met technische argumenten.
• Ik ontwerp en programmeer schaalbare cloud infrastructuur via Terraform code, waarbij ik specifiek Google cloud run en Cloud SQL in plaats van handmatige virtuele machines, om een reproduceerbare omgeving te garanderen.
• Ik pas geavanceerde security concepten toe, zoals het inrichten van Workload Identity Federation voor GitLab CI/CD pijplijnen, om data tijdens verzending en beheerdersrechten strikt te beveiligen volgens het least-privilege principe.

# Bewijsstukken
Om mijn leerdoelen aan te tonen, lever ik het volgende op:
1. Onderzoeksdocument over integratie: Een technisch verslag met mijn vergelijking tussen REST, Server-Sent Events en MCP. Ik beschrijf mijn testopstellingen en de harde technische argumenten waarom ik SSE uitsluit en kies voor een strakke REST API. (Analysis)
2. Architectuurdiagram: Een netwerkschema dat exact toont hoe de chat-interface via HTTPS verbindt met de Cloud run backend, hoe de backend praat met de database via Cloud SQL, en welke IAM veiligheidsregels we toepassen op deze verbindingen. (Analysis)
3. Infrastructure as Code repository: De volledige broncode van mijn Dockerfiles en Terraform scripts, inclusief een gedetailleerde README met de exacte terminal commando's om de gehele Google Cloud omgeving vanaf nul geautomatiseerd op te bouwen. (Realise)
4. Security configuratieverslag: Een document waarin ik samen met de security engineer met codevoorbeelden aantoon hoe Workload Identity Federation is geconfigureerd in onze pijplijn. (Realise)

# Activiteiten en microplanning
• Week 1: Ik doe praktijkonderzoek naar REST en de alternatieven. Ik bouw lokale testscripts om te bevestigen dat een REST API het meest stabiel is voor onze Cloud Run setup. Ik start mijn onderzoeksdocument waarin ik noteer waarom deze techniek het beste werkt voor onze specifieke infrastructuur.
• Week 2: Ik schrijf de Dockerfiles voor de backend en de chat-interface. Samen met de security engineer richt ik Workload Identity Federation in op GitLab en testen we of de lokale containers veilig en versleuteld met elkaar communiceren.
• Week 3: Ik schrijf alle benodigde Terraform scripts om de Cloud SQL database en Cloud Run diensten op te zetten. Ik push de infrastructuur naar Google Cloud, los de laatste netwerkfouten op en rond mijn architectuurdiagram en documentatie af voor de oplevering.
