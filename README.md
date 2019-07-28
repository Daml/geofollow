geofollow
=========

L'objectif initial était la synchro non bloquante de la vue d'un QGIS à partir de celle d'un utilisateur dans [NETGEO](https://www.gismartware.com/en/solutions-en/netgeo-telecom/). Les deux étant en Lambert 93 (EPSG:2154).

Pour l'instant seul QGIS 2.18 est supporté.

Serveur
-------

Ecrit en `go` c'est un broadcaster basique :

* En HTTP (port `13728`) pour :
    * Un faux service WMS pour publier la BBOX depuis l'application choisie.
    * Un service `Websocket` pour lire le flux depuis le web.
* En TCP brut (port `13729`) pour :
    * Permettre au plugin QGIS de lire le flux sans nécessiter une lib websocket qui n'est pas dispo sur l'installation standard.

QGIS
----

Un plugin `python` permet de se connecter/déconnecter du serveur.

Les coordonnées reçues sont reprojetées à la volée (si l'info est correcte, attention avec Leaflet).

La gestion de la connection est dans un thread dédié mais l'intervention sur le canvas est dans le corps du plugin, ça semble être la bonne approche pour un bon rafraichissement.

Web
---

Deux exemples avec Leaflet sont disponibles :
* Un master publiant sa bbox vers le faux serveur WMS. Bricolage sur `moveend` car Leaflet cherche des tuiles sur son `WMSLayer` et non une vue d'ensemble.
* Un client suivant un flux.

Raw
---

Vous pouvez suivre un feed brut :

    echo "web" | nc localhost 13729 | jq

Todo
----

* Tests QGIS 3
* Rétention de la dernière position transmise par flux pour envoi immediat au lecteur qui se connecte.
* Log fichier exploitable
