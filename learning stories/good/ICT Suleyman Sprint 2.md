Learning Story Sprint 2: DevSecOps & Automated Identity
1. Context
In Sprint 1 heb ik de basis van GCP Secret Manager handmatig verkend. Om dit project naar een professioneel niveau te tillen binnen mijn Security-profiel, is handmatige configuratie niet langer voldoende. Het is onveilig en niet transparant.
Mijn uitdaging deze sprint is het bouwen van een geautomatiseerde beveiligingsstraat. Ik ga de infrastructuur (IAM-rollen en Secrets) vastleggen in Terraform en deze laten uitrollen via een GitLab CI/CD pipeline. Hiermee creëer ik een "Audit Trail": elke wijziging in wie bij welke API-keys mag, wordt gelogd in Git. Dit sluit direct aan bij de behoefte van het project om een robuuste en veilige omgeving te hebben voor de AI-feedback-loops.
2. Mijn Aanpak
Ik ga een brug slaan tussen Cloud Security, Infrastructure as Code (IaC) en versiebeheer.
Implementatie Strategie:
Infrastructure as Code (IaC): Ik schrijf Terraform-configuraties voor de Service Accounts en Secret Manager.
GitLab CI/CD Integratie: Ik richt een pipeline in GitLab in die de Terraform-code valideert (plan) en uitvoert (apply).
OIDC / Workload Identity Federation: Ik ga onderzoeken hoe ik GitLab veilig kan laten communiceren met GCP zonder dat ik "hardcoded" JSON-keys in GitLab-variabelen hoef op te slaan. Dit is de modernste en veiligste manier van koppelen.
Wekelijks Schema:
Week 1: Terraform & Local State. Ik zet de Terraform-basis op en zorg dat ik mijn eerste Service Account via code kan aanmaken. Ik focus op de structuur van mijn .tf bestanden.
Week 2: De GitLab Connectie. Ik bouw de .gitlab-ci.yml pipeline. De grootste uitdaging hier is de authenticatie: hoe zorg ik dat GitLab "geautoriseerd" is om wijzigingen in onze GCP-omgeving aan te brengen?
Week 3: Security-as-Code Demo. Ik voltooi de pipeline. Wanneer ik een wijziging in de rechten push naar GitLab, past GCP dit automatisch aan. Ik demonstreer aan het team hoe dit zorgt voor een veilige, traceerbare werkomgeving.
3. Deliverables
Terraform-GitLab Repository: Een versiebeheerde omgeving met alle infrastructuurcode.
Geautomatiseerde Pipeline: Een werkende CI/CD workflow die infrastructuur veilig uitrolt naar GCP.
Security Architecture Diagram: Een overzicht van de connectie tussen GitLab, Terraform en de GCP-onderdelen (IAM/Secrets).
4. Persoonlijke Leerdoelen (Security & DevSecOps)
Mastering Automated Deployments: Ik wil leren hoe ik infrastructuur wijzig via een pipeline, waarbij ik de risico's van handmatige fouten minimaliseer.
Zero-Trust Pipelines: Ik wil begrijpen hoe ik GitLab toegang geef tot GCP zonder gebruik te maken van statische (onveilige) credentials, door gebruik te maken van kortstondige tokens.
Traceerbaarheid: Ik leer hoe ik Git-commits kan gebruiken als een "security log", zodat we altijd weten wie welke permissie heeft aangepast en waarom.
