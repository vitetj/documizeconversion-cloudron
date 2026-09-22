# Documize Conversion — application Cloudron

Paquet Cloudron du service de conversion Documize
([documize/conversion](https://hub.docker.com/r/documize/conversion)), le service
compagnon que Documize appelle pour **importer des documents Word** et
**générer les exports PDF**.

Documize ne sait pas faire ces deux opérations lui-même : il délègue à un
« conversion endpoint ». Par défaut il pointe vers le service partagé hébergé par
Documize ; l'éditeur recommande de l'auto-héberger et de faire pointer l'URL vers
votre propre conteneur. Ce paquet fait exactement cela, avec une URL dédiée du
type `https://apidocumize.ixapack.com`.

Version amont empaquetée : **3.4.0**.

---

## Installation

Prérequis : Cloudron 9.1 ou plus récent (`minBoxVersion` du manifeste — à
abaisser si votre serveur est plus ancien), le
[CLI Cloudron](https://docs.cloudron.io/packaging/cli/) et un accès Docker pour
construire l'image.

```bash
git clone https://github.com/vitetj/documizeconversion-cloudron
cd documizeconversion-cloudron

# 1. construire et pousser l'image dans votre registry Docker
cloudron build

# 2. installer sur le domaine voulu
cloudron install --location apidocumize --domain ixapack.com
```

L'application est ensuite accessible sur `https://apidocumize.ixapack.com`.

Pour mettre à jour le paquet plus tard : `cloudron build && cloudron update --app apidocumize.ixapack.com`.

## Configuration de Documize

Dans votre instance Documize, connectez-vous en administrateur puis renseignez
l'URL du service de conversion (réglages de l'organisation,
champ *conversion endpoint* / `ConversionEndpoint`) :

```
https://apidocumize.ixapack.com
```

C'est la seule chose à faire : l'application n'a pas d'interface web et aucun
compte à créer. Un navigateur qui ouvre l'URL est redirigé vers `documize.com`,
c'est le comportement normal du service amont.

## Vérification

```bash
curl https://apidocumize.ixapack.com/api/version
# -> 3.4.0

# test complet : conversion réelle d'un .docx
./scripts/smoke-test.sh https://apidocumize.ixapack.com mon-document.docx
```

## API exposée

| Méthode | Chemin | Rôle |
| --- | --- | --- |
| `GET` | `/api/version` | version du service (utilisé comme *health check* Cloudron) |
| `POST` | `/api/1/word` | conversion d'un `.docx`/`.doc`, champ multipart `wordfile`, réponse : archive zip contenant `result.html` |
| `POST` | `/api/plantuml` | rendu de diagrammes PlantUML |

L'export PDF n'est pas un appel direct : Documize demande au service de charger le
document dans un Chromium *headless* (via `puppet.js`), qui imprime la page en PDF.
Le service a donc besoin de pouvoir joindre votre instance Documize en HTTP(S).

## Comment le paquet est construit

Le service amont n'est distribué que sous forme d'image Docker (pas de code
source publié). Le `Dockerfile` utilise donc une construction multi-étapes : les
artefacts sont extraits de `documize/conversion:3.4.0` puis réassemblés sur
`cloudron/base:5.1.0` (Ubuntu 24.04) :

* `api-linux` — le serveur HTTP en Go ;
* `java/` — `documize.jar` + les bibliothèques Aspose Words/PDF et PlantUML,
  exécutées avec l'OpenJDK 11 installé depuis les dépôts Ubuntu ;
* `puppet.js` + `node_modules/` — l'export PDF, avec le Chromium 101 livré par
  puppeteer, lancé par le Node.js de l'image de base ;
* les polices TrueType livrées par l'amont (Arial, Times New Roman, …), sans
  lesquelles la mise en page des documents convertis dérive.

Particularités d'exécution, gérées par `start.sh` :

* `api-linux` cherche `java/` et `puppet.js` **relativement à son répertoire de
  travail** et y écrit son journal PDF. Comme `/app/code` est en lecture seule sur
  Cloudron, le démarrage crée `/run/documize` (inscriptible) avec des liens
  symboliques vers le code, et lance le service depuis ce répertoire.
* Les fichiers temporaires de conversion vont dans `/app/data/tmp` (via `TMPDIR`)
  et non dans `/tmp`, qui est un tmpfs de taille réduite : un `.docx` volumineux
  le remplirait. Le résidu d'une exécution précédente est purgé au démarrage.
* Le service tourne en `cloudron:cloudron` (via `gosu`), jamais en root.

## Ressources

`memoryLimit` est fixé à **2 Go** : la conversion Word lance une JVM avec
`-Xmx1000m` et l'export PDF un Chromium. En dessous, les conversions de gros
documents échouent. La valeur est ajustable dans l'interface Cloudron.

L'image fait environ 3,6 Go, dont ~370 Mo de polices et ~500 Mo pour le Chromium
de puppeteer. Pour une image plus légère, au prix de la fidélité de rendu,
supprimez du `Dockerfile` la copie des polices amont (les polices Liberation
installées par `apt` prennent alors le relais).

Les polices reprises de l'image amont sont des polices Microsoft : leur
redistribution suit le même régime que l'image `documize/conversion` dont elles
proviennent. Le fichier `java/Aspose.Total.Java.lic` est également fourni par
l'amont.

## Sécurité

**L'API de conversion n'est pas authentifiée**, parce que Documize l'appelle de
serveur à serveur sans identifiants — c'est le fonctionnement du service amont, pas
un choix de ce paquet. Toute personne connaissant l'adresse peut donc envoyer un
document à convertir. Si l'endpoint n'a pas besoin d'être public, restreignez-y
l'accès au niveau du pare-feu / du reverse proxy, en laissant passer l'IP de votre
serveur Documize.

À noter aussi : le code amont date de 2022 (Chromium 101, Node.js utilisé
uniquement en local pour le rendu). Il n'est pas maintenu par ce paquet.

## Contenu du dépôt

```
CloudronManifest.json   manifeste de l'application
Dockerfile              construction multi-étapes depuis l'image amont
start.sh                préparation du runtime et lancement du service
DESCRIPTION.md          description affichée par Cloudron
POSTINSTALL.md          message affiché après installation
CHANGELOG.md            journal des versions du paquet
logo.png                icône 256x256
scripts/smoke-test.sh   test de bout en bout (santé + conversion réelle)
scripts/make-logo.py    génération de l'icône
```

## Tests effectués

L'image a été construite et lancée localement (Docker, réseau hôte, volume
`/app/data`) :

* `GET /api/version` → `200 3.4.0` (health check Cloudron) ;
* conversion d'un `.docx` réel via `POST /api/1/word` → `200`, archive zip
  contenant `result.html` (journal du service : *« run Aspose java, read MHTML
  file … Success »*) ;
* génération d'un PDF avec puppeteer + le Chromium livré, sous l'utilisateur
  `cloudron` ;
* service confirmé en écoute sur le port 5010, exécuté en tant que `cloudron`,
  polices Arial et Times New Roman résolues par fontconfig.

L'installation sur un Cloudron réel (`cloudron build` / `cloudron install`) n'a pas
pu être exécutée depuis cet environnement.
