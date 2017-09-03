# -*- coding: utf-8 -*-

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import numpy as np
import csv
from qgis.core import *
from qgis.gui import *
from qgis.networkanalysis import *
import processing
from random import randint


"""script permettant de créer des fichiers forme "shp" des trajets calculés
"""


def dijkstra(depart,arrivee,k):


	#depart : point qgis
	#arrivee : liste de point qgis

	#pour un calcul de distance réel il faut mettre les coordonnées en wgs84
	
	#liste contenant toutes les distances calculées lors du calcul
	dist = np.zeros(len(arrivee))
	#compteur qui va servir pour remplir la liste dist
	i = 0
	
	#notre systeme de coordonnées
	crs = qgis.utils.iface.mapCanvas().mapRenderer().destinationCrs()

	#adresse de départ
	pStart = depart #on vas ici faire en sorte que l'utilisateur entre des coordonnées

	#adresses collèges
	pStop = arrivee#ne change pas
	list_rb = []
	
	for l in pStop:

		vLayer = qgis.utils.iface.mapCanvas().currentLayer()


		director = QgsLineVectorLayerDirector(vLayer, -1, '', '', '', 3)


		properter = QgsDistanceArcProperter()


		director.addProperter(properter)


		
		builder = QgsGraphBuilder(crs)






		tiedPoints = director.makeGraph(builder, [pStart, l])
		graph = builder.graph()

		tStart = tiedPoints[0]
		tStop = tiedPoints[1]

		idStart = graph.findVertex(tStart)
		idStop = graph.findVertex(tStop)

		(tree, 	cost) = QgsGraphAnalyzer.dijkstra(graph, idStart, 0)


		#coueur aléatoire
		color = QColor.fromRgb(randint(0,250),randint(0,250),randint(0,250))
		
		if tree[idStop] == -1:
		  print ("Path not found")
		else:
		  p = []
		  curPos = idStop
		  while curPos != idStart:
			p.append(graph.vertex(graph.arc(tree[curPos]).inVertex()).point())
			curPos = graph.arc(tree[curPos]).outVertex();

		  p.append(tStart)

		  rb = QgsRubberBand(qgis.utils.iface.mapCanvas())	  
		  rb.setColor(color)
		  qgis.utils.iface.mapCanvas().scene().removeItem(rb)
		  
		  
			
		  for pnt in p:
			
			rb.addPoint(pnt)
			
			
		  list_rb.append(rb)
		  
			
		  trajet = rb.asGeometry()
		  dist[i] = trajet.length()
		  
		  
		  
		  print (dist[i] , list[i][0])
		  i+=1
		  
	#on ordonne la matrice : le premier sera la dist la plus courte..
	
	#matrice d'indices rangés dans l'ordre croissant
	sort_mat = np.argsort(dist)
	#indice de la distance la plus faible
	premier_col_i = sort_mat[0]
	#distance ratachée
	dist_premier_col = dist[sort_mat[0]]
	#pareil
	deuxieme_col_i = sort_mat[1]
	dist_deuxieme_col = dist[sort_mat[1]]

	#création de couches pour les trajets
	rubtolayer(list_rb[premier_col_i],str(list[premier_col_i][0]))
	rubtolayer(list_rb[deuxieme_col_i],str(list[deuxieme_col_i][0]))
	
def rubtolayer(rub,nom):


	#on transforme notre rubber en geom pour créer une couche
	geom = rub.asGeometry()
	poly = geom.asPolyline()
	layer =  QgsVectorLayer('LineString', nom  , "memory")
	pr = layer.dataProvider() 
	feat = QgsFeature()
	feat.setGeometry(QgsGeometry.fromPolyline(poly))
	pr.addFeatures([feat])
	layer.updateExtents()
	QgsMapLayerRegistry.instance().addMapLayers([layer])

	
	
def compute():
	##création du fichier CSV pour les résultats, c'est le main qu'on va utiliser pour l'interface graphique
	
	resultat = open("C:\Users\ajlsi\Desktop\Scripts\resultat_mc_mp.csv","w")
	
	
	#permet d'effectuer la transformation de wgs84 en lambert pour le calcul
	crsSrc = QgsCoordinateReferenceSystem(4326)    # lambert
	crsDest = QgsCoordinateReferenceSystem(2154)  # WGS 84 / UTM zone 33N
	xform = QgsCoordinateTransform(crsSrc, crsDest) 


	#pour lire les csv contenant les adresses et collèges
	adresses = open("C:\Users\ajlsi\Desktop\Scripts\adresses_smc.csv","r")
	colleges = open("C:\Users\ajlsi\Desktop\Scripts\colleges.csv","r")
	csv_1 = csv.reader(adresses)
	csv_2 = csv.reader(colleges)

	#initialisation des listes
	
	#liste collèges avec nom et coordo avec doublons
	list = []
	
	#liste des collèges sans doublons
	list_colleges = []
	
	#liste des eleves avec leur id et coordo
	list_eleves = []
	
	#liste de points qgis pour les collèges
	pnts_colleges = []
	
	
	j = 0

			
	
		
	###liste des colleges (adresse,lat,lng) et eleves (id,lat,lng) ici on s'occupe juste des élèves des collèges Marie Curie et Gerard Philipe
	for row in csv_1: 
			
		if(row[7] == 'GERARD PHILIPE' or row[7] == 'MARIE CURIE' ) :
			list_eleves.append((row[0],row[1],row[2],row[3],row[5],row[4]))

	for row in csv_2: 	
		list_colleges.append((row[0],row[2],row[1]))
	
	del(list_colleges[0])#on supprime la première ligne des entêtes
	
	#initialisation de la matrice qui va permettre de choisir des élèves au hasard pour la démo
	#demo = np.random.choice(len(list_eleves)-1,2)
	
	###création de liste des points des collèges:
	for elem in list_colleges:
		if elem not in list:
			list.append(elem)
	
	for college in list:
		
		pnt = xform.transform(QgsPoint(float(college[1]),float(college[2])))
		pnts_colleges.append(pnt)
	
	#chargement de la carte des voies
	# total list of layers actually displayed on map canvas
	canvas_layers = []
	
	if(len(QgsMapLayerRegistry.instance().mapLayersByName('TRONCON_VOIE_PARIS')) == 0):
		# load vector layers
		vlayer = QgsVectorLayer("C:\Users\ajlsi\Desktop\Scripts\TRONCON_VOIE_PARIS\TRONCON_VOIE_PARIS.shp", "TRONCON_VOIE_PARIS", "ogr")
		vlayer.setLayerTransparency(70)

		# add the layer to the registry
		QgsMapLayerRegistry.instance().addMapLayer(vlayer)
	

	
	
	
	for elemn in list_eleves:

			
		depart = xform.transform(QgsPoint(float(elem[4]),float(elem[5])))#transformation des coordo de départ = adresses eleves en point qgis
		dijkstra(depart,pnts_colleges,k) #algo
		

		
		
		

		
		
	resultat.close()
