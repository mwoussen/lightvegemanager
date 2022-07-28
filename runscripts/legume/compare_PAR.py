import sys
import os

import numpy as np
from scipy import array

try :
    from src.LightVegeManager import *
    from src.l_egume_template import *

except ModuleNotFoundError:
    # ajoute le dossier lightvegemanager dans le sys.path
    sys.path.insert(1, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
    from src.LightVegeManager import *
    from src.l_egume_template import *

## --> Installer la dernière version de lpy (3.9.2) pour la cohabitation cnwheat et legume

### on vérifie le transfert de la grille entre l-egume et RATP

# Note : l-egume même convention que RATP?
# scene géométrique en cm MAIS surface foliaire (dans m_lais) en m²
# plantgl commence un peu sous z=0.
# taille des voxels et nb de voxels dans la scène recalculés dans l-egume à partir des dimensions de la scène
# si pyratp.init -> plantgl.init -> pyratp.run : plante car objets de lvm.pyratp corrompus

### ETAPES
# chemin des inputs
# ouvre le excel usm et l'enregistre dans un dico
# fait une liste de lsystem pour chaque situation de l'usm to_run==1 

foldin = "C:/Users/mwoussen/cdd/codes/vegecouplelight/l-egume/legume/input/"
foldout = "C:/Users/mwoussen/cdd/codes/vegecouplelight/outputs/legume/"
fusms = "liste_usms_exemple.xls"
ongletBatch = "exemple"

# prépare une liste de l-system à lancer
lsystem_simulations, names_simulations = initialisation_legume(foldin, foldout, fusms, ongletBatch)

index_simulation = 0
sim_id = names_simulations[index_simulation]
lstring = lsystem_simulations[sim_id].axiom
nb_iter = lsystem_simulations[sim_id].derivationLength #lire dans derivation_length #335 #30
lsystem_simulations[sim_id].opt_external_coupling = 1 # met a un l'option external coupling

# copie du lsystem pour récupérer la taille des voxels
lsys_temp = lsystem_simulations[sim_id]
lstring_temp = lsys_temp.derive(lstring, 0, 1)
# récupère toutes les variables du lsystem
tag_loop_inputs = lsystem_simulations[sim_id].tag_loop_inputs
invar, outvar, invar_sc, ParamP, \
    station, carto, meteo_j, mng_j,  \
    DOY, cutNB, start_time, nbplantes,  \
    surfsolref, m_lais, dicFeuilBilanR,  \
    surf_refVOX, triplets, ls_dif, S, par_SN,  \
    lims_sol, ls_roots, stateEV, Uval, b_,  \
    ls_mat_res, vCC, ls_ftswStress, ls_NNIStress,  \
    ls_TStress, lsApex, lsApexAll, dicOrgans,  \
    deltaI_I0, nbI_I0, I_I0profilLfPlant, I_I0profilPetPlant,  \
    I_I0profilInPlant, NlClasses, NaClasses, NlinClasses,  \
    opt_stressW, opt_stressN, opt_stressGel, opt_residu = tag_loop_inputs
dxyz = lsys_temp.dxyz # récupère nouvelle taille de voxel
nxyz = lsys_temp.na # récupère le nombre de voxels

## INITIALISATION LIGHTVEGEMANAGER
environment = {}
ratp_parameters_legume = {}
ratp_parameters_plantgl = {}
caribu_parameters = {}

# Paramètres pré-simulation
environment["names"] = ["l-egume"]
environment["coordinates"] = [46.43,0,0] # latitude, longitude, timezone
environment["sky"] ="turtle46" # ["file", "runscripts/legume/sky_5.data"] # "turtle46" # turtle à 46 directions par défaut
environment["diffus"] = True
environment["direct"] = False
environment["reflected"] = False
environment["reflectance coefficients"] = [[0., 0.]]
environment["infinite"] = False

## PARAMETRES RATP scene grille l-egume ##
ratp_parameters_legume["voxel size"] = [d*0.01 for d in dxyz]
ratp_parameters_legume["soil reflectance"] = [0., 0.]
ratp_parameters_legume["mu"] = [1.]
ratp_parameters_legume["origin"] = [0., 0., 0.]

lghtratp_legume = LightVegeManager(environment=environment,
                                lightmodel="ratp",
                                lightmodel_parameters=ratp_parameters_legume,
                                main_unit="m")

## PARAMETRES RATP scene PlantGL ##
ratp_parameters_plantgl["voxel size"] = [d*0.01 for d in dxyz]
ratp_parameters_plantgl["xy max"] = lsys_temp.cote
ratp_parameters_plantgl["soil reflectance"] = [0., 0.]
ratp_parameters_plantgl["mu"] = [1.]
ratp_parameters_plantgl["tesselation level"] = 2
ratp_parameters_plantgl["angle distrib algo"] = "file"
ratp_parameters_plantgl["angle distrib file"] = "runscripts/legume/luzerne_angle_distrib.data"
# ratp_parameters_plantgl["origin"] = [0., 0., dxyz[2] * nxyz[2]] # [0., 0.]
# ratp_parameters_plantgl["grid slicing"] = "ground = 0."

lghtratp_plantgl = LightVegeManager(environment=environment,
                                lightmodel="ratp",
                                lightmodel_parameters=ratp_parameters_plantgl,
                                main_unit="m")

# début de la simulation
for i in range(nb_iter+1):
    print('time step: ',i)
    lstring = lsystem_simulations[sim_id].derive(lstring, i, 1)
    
    # récupère toutes les variables du lsystem
    tag_loop_inputs = lsystem_simulations[sim_id].tag_loop_inputs
    invar, outvar, invar_sc, ParamP, \
        station, carto, meteo_j, mng_j,  \
        DOY, cutNB, start_time, nbplantes,  \
        surfsolref, m_lais, dicFeuilBilanR,  \
        surf_refVOX, triplets, ls_dif, S, par_SN,  \
        lims_sol, ls_roots, stateEV, Uval, b_,  \
        ls_mat_res, vCC, ls_ftswStress, ls_NNIStress,  \
        ls_TStress, lsApex, lsApexAll, dicOrgans,  \
        deltaI_I0, nbI_I0, I_I0profilLfPlant, I_I0profilPetPlant,  \
        I_I0profilInPlant, NlClasses, NaClasses, NlinClasses,  \
        opt_stressW, opt_stressN, opt_stressGel, opt_residu = tag_loop_inputs                    
    
    ############
    # step light transfer coupling
    ############

    # PAR / Blue voxel
    tag_light_inputs = [m_lais / surf_refVOX, triplets, ls_dif, meteo_j['I0'] * surf_refVOX]  # input tag

    # mise a jour de res_trans, res_abs_i, res_rfr, ls_epsi
    local_res_trans, local_res_abs_i = riri.calc_extinc_allray_multi_reduced(*tag_light_inputs, optsky=station['optsky'], opt=station['sky'])

    # transfert des sorties
    ## TRES LENT !!
    # res_abs_i = np.zeros((m_lais.shape[0], nxyz[2], nxyz[1], nxyz[0]))
    # res_trans = np.zeros((nxyz[2], nxyz[1], nxyz[0]))
    # for ix in range(nxyz[0]):
    #     for iy in range(nxyz[1]):
    #         for iz in range(nxyz[2]):
    #             vox_data = lghtratp_legume.voxels_outputs[(lghtratp_legume.voxels_outputs.Nx == ix+1) &  
    #                                                                     (lghtratp_legume.voxels_outputs.Ny == iy+1) &
    #                                                                     (lghtratp_legume.voxels_outputs.Nz == iz+1)]
                
    #             res_trans[iz, iy, ix] = (1 - sum(vox_data["xintav"]))
    #             for ie in range(m_lais.shape[0]) :
    #                 if len(vox_data) > 0 :
    #                     res_abs_i[ie, iz, iy, ix] = vox_data[vox_data.VegetationType == ie+1]["PARa"].values[0]

    iteration_legume_withoutlighting(lsystem_simulations[sim_id], local_res_trans, local_res_abs_i, tag_loop_inputs)

print((''.join((sim_id, " - done"))))

## Paramètres météo ## 
doy = lsystem_simulations[sim_id].meteo["DOY"][i]
hour = 12
energy = meteo_j['I0']

# Refait le dernier calcul de rayonnement
tag_light_inputs = [m_lais / surf_refVOX, triplets, ls_dif, energy*surf_refVOX]  # input tag
res_trans, res_abs_i = riri.calc_extinc_allray_multi_reduced(*tag_light_inputs, optsky=station['optsky'], opt=station['sky'])

# combien/quelles lignes a zeros de LAI au dessus
laicum = np.sum(m_lais, axis=0)
laicumvert = np.sum(laicum, axis=(1, 2))
nb0 = 0  # nb de couches sans feuilles/LAI
for i in range(len(laicumvert)):
    if laicumvert[i] == 0.:
        nb0 += 1
    else:
        break

# ajouter un if sur nb0 ou le faire a chaque fois?
# redim des m_lai et triplets
shp = np.shape(m_lais)
reduced_mlai = []
for plt in range(shp[0]):
    reduced_mlai.append(m_lais[plt, (nb0 - 1):shp[1], :, :])

reduced_mlai = array(reduced_mlai)

## Paramètres scene ##
# Surface foliaire et distribution des angles de l-egume
scene_legume = {}
scene_legume["LA"] = m_lais # /np.prod(np.array(ratp_parameters_legume["voxel size"]))
scene_legume["distrib"] = ls_dif

# récupère la scène PlantGL
scene_plantgl = lsystem_simulations[sim_id].sceneInterpretation(lstring)

# Scene PlantGL feuilles
geometry = {}
geometry["scenes"] = [scene_plantgl]
geometry["transformations"] = {}
geometry["transformations"]["scenes unit"] = ["cm"]
geometry["transformations"]["xyz orientation"] = ["y+ = y-"]

lghtratp_plantgl.init_scenes(geometry)
lghtratp_plantgl.run(PARi=energy, day=doy, hour=hour, truesolartime=True, parunit="RG")
# impression du plantGL et de sa grille
# lghtratp_plantgl.VTKinit(foldout+"plantgl")

# Transfert grille l-egume vers RATP
geometry = {}
geometry["scenes"] = [scene_legume]

lghtratp_legume.init_scenes(geometry)
lghtratp_legume.run(PARi=energy, day=doy, hour=hour, truesolartime=True, parunit="RG")
# lghtratp_legume.VTKinit(foldout+"legume", printtriangles=False)

# détail des LAD par voxel
leg_aire = []
ratp_aire = []
plantgl_aire = []
diff_ratp=[]
diff_plantgl=[]
para_legume=[]
part_legume=[]
para_ratp=[]
part_ratp=[]
para_plantgl=[]
part_plantgl=[]
t_nx=[]
t_ny=[]
for i in range(m_lais.shape[1]):
    for j in range(m_lais.shape[2]):
        for k in range(m_lais.shape[3]):
            if m_lais[0][i][j][k] > 0. :
                vox_legume = lghtratp_legume.voxels_outputs[(lghtratp_legume.voxels_outputs.Nx==k+1) & 
                                                            (lghtratp_legume.voxels_outputs.Ny==j+1) & 
                                                            (lghtratp_legume.voxels_outputs.Nz==i+1)]

                vox_plantgl = lghtratp_plantgl.voxels_outputs[(lghtratp_plantgl.voxels_outputs.Nx==k+1) & 
                                                            (lghtratp_plantgl.voxels_outputs.Ny==j+1) & 
                                                            (lghtratp_plantgl.voxels_outputs.Nz==1)]                
                
                t_nx.append(k+1)
                t_ny.append(j+1)
                leg_aire.append(m_lais[0][i][j][k])
                ratp_aire.append(vox_legume["Area"].values[0])
                plantgl_aire.append(vox_plantgl["Area"].values[0])
                diff_ratp.append(100*abs(m_lais[0][i][j][k] - vox_legume["Area"].values[0])/m_lais[0][i][j][k])
                diff_plantgl.append(100*abs(m_lais[0][i][j][k] - vox_plantgl["Area"].values[0])/m_lais[0][i][j][k])
                para_legume.append(res_abs_i[0][i][j][k])
                part_legume.append(res_trans[i][j][k])
                para_ratp.append(energy * vox_legume[vox_legume.VegetationType == 1]["xintav"].values[0])
                part_ratp.append(energy * sum(vox_legume["transmitted"]))
                para_plantgl.append(energy * vox_plantgl[vox_plantgl.VegetationType == 1]["xintav"].values[0])
                part_plantgl.append(energy * sum(vox_plantgl["transmitted"]))

df_compare = pandas.DataFrame({"Nx" : t_nx, "Ny" : t_ny, 
                            "l-egume" : leg_aire, 
                            "lvm ratp" : ratp_aire, 
                            "lvm plantgl" : plantgl_aire, 
                            "% ecart ratp" : diff_ratp, 
                            "% ecart plantgl" : diff_plantgl,
                            "PARa legume" : para_legume,
                            "PARa ratp" : para_ratp,
                            "PARa plantgl" : para_plantgl,
                            "PARt legume" : part_legume,
                            "PARt ratp" : part_ratp,
                            "PARt plantgl" : part_plantgl})
print(df_compare)
print("\n")
print(" --- Surface Foliaire totale m^2---")
print("l-egume : ", sum(df_compare["l-egume"]))
print("lvm ratp", sum(df_compare["lvm ratp"]))
print("plantgl feuilles", sum(df_compare["lvm plantgl"]))
print("\n")
lsystem_simulations[sim_id].clear()