'''
    LightVegeManager_sky
    ********************

    Build a sky from LightVegeManager input informations

    Possible sky options:
        - ``"turtle46"`` : soc sky composed by 46 directions in a turtle shape
        - filepath : string indicating a file path
        - ``[nb_azimut, nb_zenith, "soc" or "uoc"]`` : build a sky with a custom number of directions

    output :
        - with RATP : pyratp.skyvault
        - with CARIBU : [(weight, (dir[0], dir[1], dir[2])), ... ]

    Sky file is in RATP format
'''
from alinea.pyratp.skyvault import Skyvault
from alinea.caribu.sky_tools import turtle
from alinea.caribu.sky_tools import GenSky
from alinea.caribu.sky_tools import GetLight

import math
import numpy as np



def RATPsky(skytype) :
    """Creates a pyratp.skyvault

    :param skytype: the environment["sky"] from the LightVegeManager inputs. It is either:
        * ``"turtle46"``
        * a filepath
        * [nb_azimut, nb_zenith, "soc" or "uoc"], nb_azimut is the number of azimut directions and nb_zenith the number of zenital directions for cutting out the sky
    :type skytype: string or list
    :raises ValueError: if skytype is not one of the curretn 3 possibilities
    :return: a sky in RATP format
    :rtype: pyratp.skyvault
    """    
    input_sky = skytype
    output_sky = []

    if input_sky == "turtle46" : output_sky = Skyvault.initialise()
    elif isinstance(input_sky, str) and \
        input_sky != "turtle46" :
        output_sky = Skyvault.read(input_sky)

    elif isinstance(input_sky, list) and \
        len(input_sky) == 3 :
        ele, \
        azi,  \
        omega, \
            pc = discrete_sky(input_sky[0],  \
                                input_sky[1], \
                                input_sky[2])
        output_sky = Skyvault.initialise(ele, azi, omega, pc)
    
    else :
        raise ValueError("Unknown sky parameters : can be either \
                            'turtle46' or a string filepath or    \
                            [nb_azimut, nb_zenith, 'soc' or 'uoc'] ")
    
    return output_sky


def CARIBUsky(skytype) :
    """Build a sky in CARIBU format

    :param skytype: the environment["sky"] from the LightVegeManager inputs. It is either:
        * ``"turtle46"``
        * a filepath
        * [nb_azimut, nb_zenith, "soc" or "uoc"], nb_azimut is the number of azimut directions and nb_zenith the number of zenital directions for cutting out the sky
    :type skytype: string or list
    :raises ValueError: if skytype is not one of the curretn 3 possibilities
    :return: a list of the directions representing the sky.
    each entry of the list is a tuple (weight, vector), where weight is a float for the weight the direction and vector, a tuple (x, y, z), 
    representing the position of the sky direction, from sky to the ground
    :rtype: list of tuple
    """    
    input_sky = skytype
    output_sky = []

    # first option turtle of 46 directions
    if input_sky == "turtle46":
        turtle_list = turtle.turtle()
        output_sky = []
        for i,e in enumerate(turtle_list[0]):
            dir = turtle_list[2][i]
            t = tuple((e, tuple((dir[0], dir[1], dir[2]))))
            output_sky.append(t)

    # read a sky file
    elif isinstance(input_sky, str) and \
        input_sky != "turtle46" :
        
        listGene = []
        f = open(input_sky)
        ndir=int(f.readline().strip().split('\t')[0])
        hmoy=np.zeros(ndir)
        azmoy=np.zeros(ndir)
        omega=np.zeros(ndir)
        pc=np.zeros(ndir)
        for n in range(ndir):
            listGene.append(f.readline().strip().split('\t'))
        tabGene=np.array(listGene)
        tabGene = np.cast['float64'](tabGene)
        hmoy=np.transpose(tabGene)[0]*math.pi / 180
        azmoy=np.transpose(tabGene)[1]*math.pi / 180
        omega=np.transpose(tabGene)[2]
        pc=np.transpose(tabGene)[3]
        f.close()
        
        # converts in CARIBU format (azimut, zenit) -> (x, y, z)
        output_sky = []
        for i, p in enumerate(pc) :
            dir=[0,0,0]
            dir[0] = dir[1] = math.sin(hmoy[i])
            dir[0] *= math.cos(azmoy[i])
            dir[1] *= math.sin(azmoy[i])
            dir[2] = -math.cos(hmoy[i])
            t = tuple((float(p), tuple((dir[0], dir[1], dir[2]))))
            output_sky.append(t)

    elif isinstance(input_sky, list) and \
        len(input_sky) == 3 :
        #: (Energy, soc/uoc, azimuts, zenits)
        sky_string = GetLight.GetLight(GenSky.GenSky()(1., input_sky[2], 
                                                            input_sky[0], 
                                                            input_sky[1]))  

        for string in sky_string.split('\n'):
            if len(string) != 0:
                string_split = string.split(' ')
                t = tuple((float(string_split[0]), 
                            tuple((float(string_split[1]), 
                                    float(string_split[2]), 
                                    float(string_split[3])))))
                output_sky.append(t)

    else :
        raise ValueError("Unknown sky parameters : can be either \
                            'turtle46' or a string filepath or    \
                            [nb_azimut, nb_zenith, 'soc' or 'uoc'] ")
                            
    return output_sky


def writeskyfile(h, az, omega, weights, filepath) :
    """Writes a file with sky information, readable by LightVegeManager

    :param h: Elevation angle (degrees) pointing to the center of a sky fraction
    :type h: list of float
    :param az: Azimuth angle (degrees) pointing to the center of a sky fraction
    :type az: list of float
    :param omega: Solid angle associated to the direction of incidence
    :type omega: list of float
    :param weights: Relative contribution of the sky fraction to the sky illumination)
    :type weights: list of float
    :param filepath: name of the file to write
    :type filepath: list of float
    """    
    # TODO: write it
    return


def discrete_sky(n_azimuts, n_zeniths, sky_type) :
    """Cuts out a sky following input number of directions

    :param n_azimuts: number of azimut directions of the sky
    :type n_azimuts: int
    :param n_zeniths: number of zenital directions of the sky
    :type n_zeniths: int
    :param sky_type: ``"soc"`` or ``"uoc"`` 
    :type sky_type: string
    :return: 4 output lists of length n_azimuts * n_zeniths
        * ele: elevations in degrees (angle soil to sky)
        * azi: azimuts in degrees
        * omega: solid angle of directions
        * pc: relative contribution of directions to incident diffuse radiation
    :rtype: list, list, list, list
    """    

    # TODO: doesn't work properly
    ele=[]
    azi=[]
    da = 2 * math.pi / n_azimuts
    dz = math.pi / 2 / n_zeniths    
    todeg = 180/math.pi          
    for j in range(n_azimuts):
        for k in range(n_zeniths):
            azi.append((j * da + da / 2)*todeg)
            ele.append((k * dz + dz / 2)*todeg)
    n = n_azimuts*n_zeniths
    
    omega=[2*math.pi/n]*n
    
    def uoc (teta, dt, dp):
        """ teta: angle zenithal; phi: angle azimutal du soleil """
        dt /= 2.
        x = math.cos(teta-dt)
        y = math.cos(teta+dt)
        E = (x*x-y*y)*dp/2./math.pi
        return E
    def soc (teta, dt, dp):
        """ teta: angle zenithal; phi: angle azimutal du soleil """
        dt /= 2.
        x = math.cos(teta-dt)
        y = math.cos(teta+dt)
        E = (3/14.*(x*x-y*y) + 6/21.*(x*x*x-y*y*y))*dp/math.pi
        return E
    pc=[]
    for j in range(n_azimuts):
        for k in range(n_zeniths):
            azim, elv = j * da + da / 2, k * dz + dz / 2
            I=0
            if(sky_type=='soc'):
                I = soc(elv, dz, da)
            elif (sky_type=='uoc'):
                I = soc(elv, dz, da)
    return ele, azi, omega, pc