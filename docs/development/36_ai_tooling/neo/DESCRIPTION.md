<!--
  Kurzbeschreibung fuer den Discord-Bot "Neo - Nachtforscher"
  (Discord Developer Portal -> Allgemeine Informationen -> Beschreibung).
  Kein automatischer Sync, bei einer Aenderung im Portal hier nachziehen.
-->

BitGridAI Nachtforscher: lokaler Analyse-Agent der Solar-Mining-Anlage.
Wertet nachts die Energie- und Miningdaten des Vortags aus, sucht
Optimierungspotenzial (SoC-Baender, Modus-Effizienz in W je TH/s,
Schaltfehler, ungenutzter Ueberschuss) und schreibt Hypothesen mit
Falsifikationsbedingung nach /opt/data/nachtberichte/. Liest seine
Wissensbasis als Dateien unter /opt/data/vault/, schreibt dort nie hinein.
Laeuft auf 192.168.178.104, strikt lokal.
Rein beratend: kein Terminal, keine Code-Ausfuehrung, kein Zugriff auf die
Haussteuerung. Er schlaegt vor, der Betreiber entscheidet.
