
# parent = pynbody_analysis.py created 2021.08.11 by Stacy Kim

# selection script = created 2021.08.21 by Sushanta Nigudkar 


#import tracemalloc
#from memory_profiler import profile
import csv
import os
import pynbody
import tangos
import numpy as np
from numpy import sqrt
from darklight import DarkLight
import darklight 
from os import listdir
from os.path import *
import gc
from tangos.examples.mergers import *     
import random
import sys
import pandas as pd
from .functions_for_angular_momentum_tagging import *

def get_child_iords(halo,halo_catalog,DMOstate='fiducial'):

    children_dm = np.array([])

    children_st = np.array([])

    sub_halonums = np.array([])

    if (np.isin('children',list(halo.properties.keys())) == True) :

        children_halonums = halo.properties['children']

        sub_halonums = np.append(sub_halonums,children_halonums)

        #print(children_halonums)                                                                                                                                                                                                                              


        for child in children_halonums:

            if (len(halo_catalog[child].dm['iord']) > 0):

                children_dm = np.append(children_dm,halo_catalog[child].dm['iord'])



            if DMO_state == 'fiducial':

                if (len(halo_catalog[child].st['iord']) > 0 ):

                    children_st = np.append(children_st,halo_catalog[child].st['iord'])

            if (np.isin('children',list(halo_catalog[child].properties.keys())) == True) :

                dm_2nd_gen,st_2nd_gen,sub_halonums_2nd_gen = get_child_iords(halo_catalog[child],halo_catalog,DMOstate)

                children_dm = np.append(children_dm,dm_2nd_gen)
                children_st = np.append(children_st,st_2nd_gen)
                sub_halonums = np.append(sub_halonums,sub_halonums_2nd_gen)
            #else:                                                                                                                                                                                                                                             
            #    print("there were no star or dark-matter iord arrays")                                                                                                                                                                                        

    #else:                                                                                                                                                                                                                                                     
    #    print("did not find children in halo properties list")                                                                                                                                                                                                

    return children_dm,children_st,sub_halonums



pynbody.config["halo-class-priority"] = [pynbody.halo.hop.HOPCatalogue]

def tag_particles(sim_name,occupation_fraction,fmb_percentage,particle_storage_filename,AHF_centers_file=None,mergers = True,AHF_centers_supplied=False):
    pynbody.config["halo-class-priority"] = [pynbody.halo.hop.HOPCatalogue]
    
    #used paths
    tangos_path_edge     = '/vol/ph/astro_data/shared/morkney/EDGE/tangos/'
    tangos_path_chimera  = '/vol/ph/astro_data/shared/etaylor/CHIMERA/'
    pynbody_path_edge    = '/vol/ph/astro_data/shared/morkney/EDGE/'
    pynbody_path_chimera = '/vol/ph/astro_data/shared/etaylor/CHIMERA/'
    pynbody_edge_gm =  '/vol/ph/astro_data2/shared/morkney/EDGE_GM/'

    '''
    Halos Available

    'Halo383_fiducial'
    'Halo383_fiducial_late',   'Halo383_fiducial_288', 'Halo383_fiducial_early' 'Halo383_Massive'
    'Halo600_fiducial','Halo600_fiducial_later_mergers','Halo1445_fiducial'
    'Halo605_fiducial','Halo624_fiducial','Halo624_fiducial_higher_finalmass','Halo1459_fiducial',
    'Halo605_fiducial','Halo1459_fiducial_Mreionx02'#, 'Halo1459_fiducial_Mreionx03', 'Halo1459_fiducial_Mreionx12','Halo600_RT', 'Halo605_RT', 'Halo624_RT',
    'Halo1445_RT','Halo1459_RT'

    '''
    
    sims = [str(sim_name)]

    # open the file in the write mode
    with open(particle_storage_filename, 'w') as particle_storage_file:
        # create the csv writer
        writer = csv.writer(particle_storage_file)
        header = ['iords','mstar','t','z','type']
        # write a row to the csv file
        writer.writerow(header)



        
    # iterating over all the simulations in the 'sims' list
    for isim,simname in enumerate(sims):

        print('==================================================')
        print(simname)

        # assign it a short name
        split = simname.split('_')
        DMOstate = split[1]
        shortname = split[0][4:]
        halonum = shortname[:]
        
        if len(split) > 2:
            if   halonum=='332': shortname += 'low'
            elif halonum=='383': shortname += 'late'
            elif halonum=='600': shortname += 'lm'
            elif halonum=='624': shortname += 'hm'
            elif halonum=='1459' and split[-1][-2:] == '02': shortname += 'mr02'
            elif halonum=='1459' and split[-1][-2:] == '03': shortname += 'mr03'
            elif halonum=='1459' and split[-1][-2:] == '12': shortname += 'mr12'
            else:
                print('unsupported simulation',simname,'! Not sure what shortname to give it. Aborting...')
                continue
        elif len(split)==2 and simname[-3:] == '_RT':  shortname += 'RT'

        
        if simname[-3] == 'x':
            DMOname = 'Halo'+halonum+'_DMO_'+'Mreion'+simname[-3:]

        else:
            DMOname = 'Halo'+halonum+'_DMO' + ('' if len(split)==2 else ('_' +  '_'.join(split[2:])))

            #'Halo'+halonum+'_DMO' + ('' if len(split)==2 else ('_' +  '_'.join(split[2:]))) #if split[1]=='fiducial' else None
        
        
        # set the correct paths to data files
        if halonum == '383':
            tangos_path  = tangos_path_chimera
            pynbody_path = pynbody_path_chimera 
        else:
            tangos_path  = tangos_path_edge
            pynbody_path = pynbody_path_edge if halonum == shortname else pynbody_edge_gm
        
        # get particle data at z=0 for DMO sims, if available
        if DMOname==None:
            print('--> DMO particle does not data exists, skipping!')
            continue
        
        # listdir returns the list of entries in a given dir path (like ls on a dir)
        # isdir check if the given dir exists
        # join creates a string consisting of the path,name,entry in dir
        # once we have this string we check to see if the word 'output' is in this string (to grab only the output snapshots)
        if pynbody_path[-3:]=='x02':
            print('yes!!!!!!!')
            
        snapshots = [ f for f in listdir(pynbody_path+DMOname) if (isdir(join(pynbody_path,DMOname,f)) and f[:6]=='output') ]
        #snapshots = np.array([DMOsim.timesteps[i].__dict__['extension'] for i in range(len(DMOsim.timesteps))])[-len(halonums):]
        #sort the list of snapshots in ascending order
        snapshots.sort()
        
        # load in the DMO sim to get particle data and get accurate halonums for the main halo in each snapshot
        DMOsim,main_halo,halonums,outputs = get_the_right_halonums(DMOname,0)
        print('HALONUMS:---',len(halonums), "OUTPUTS---",len(snapshots))
        #Get stellar masses at each redshift using darklight 
        t,redshift,vsmooth,sfh_insitu,mstar_s_insitu,mstar_total = DarkLight(main_halo,DMO=True,mergers = False, poccupied=occupation_fraction)

        #calculate when the mergers took place and grab all the halo objects involved in the merger
        zmerge, qmerge, hmerge = get_mergers_of_major_progenitor(main_halo)
        
        #The redshifts and times (Gyr) of all snapshots of the given simulation
        red_all = np.array([ DMOsim.timesteps[i].__dict__['redshift'] for i in range(len(DMOsim.timesteps)) ])
        t_all = np.array([ DMOsim.timesteps[i].__dict__['time_gyr'] for i in range(len(DMOsim.timesteps)) ])

        #loop groups all the non-main halo objects that take part in mergers according to their merger's redshift.
        #this array gets stored in hmerge_added in the form - len = no. of unique zmerges, 
        # elements = all the hmerges of halos merging at this zmerge
        AHF_centers = pd.read_csv(str(AHF_centers_file)) if AHF_centers_supplied == True else None

        hmerge_added, z_set_vals = group_mergers(zmerge,hmerge)

        
        print('dkl',np.array(mstar_s_insitu))
        print(len(snapshots),'snaps length')

        ##################################################### SECOND LOOP ###############################################################
        
        selected_particles = np.array([[np.nan],[np.nan]])
        mstars_total_darklight_l = [] 
        
        # number of stars left over after selection (per iteration)
        leftover=0

        # total stellar mass selected 
        mstar_selected_total = 0

        #idrz = 9999
        print('this is how the simarray looks',pynbody.array.SimArray(10, units='pc', sim=None))
        #halonums_indexing = 0 
        with open(particle_storage_filename, 'a') as particle_storage_file:
            # looping over all snaps 
            for i in range(len(snapshots)):
                idxout = np.asarray(np.where(outputs==snapshots[i])).flatten()
                print(t_all[i],'<-- time at this snap')
                
                
                if t_all[i] >= 2:
                    print('2 gyr mark ----------------------------')
                
                if idxout.shape[0] == 0 :
                    print('no matching output found')
                    continue
                else:
                    iout = idxout[0]
                    
                # was particle data loaded in (insitu) 
                decision=False

                

                # was particle data loaded in (accreted) 
                decision2=False
                decl = False
            
                gc.collect()
            
                print('snapshot',i)

                #get the halo objects at the given timestep if and inform the user if no halos are present.
                if len(DMOsim.timesteps[i].halos[:])==0:
                    print('No halos!')
                    continue
            
                # if the output corresponding to this snap is found execute the following 
            
                # main DMO halo 
                print(DMOname+'/'+snapshots[i]+'/halo_'+str(halonums[iout]), 'halonums')
                hDMO = tangos.get_halo(DMOname+'/'+snapshots[i]+'/halo_'+str(halonums[iout]))
                #print(hDMO.keys) 
                #print(hDMO.eps)
                
                # m200 of the main halo 
                m200_main_1 = hDMO.calculate_for_progenitors('M200c')[0]

                m200_main = m200_main_1[0] if len(m200_main_1)>0 else 0

                #print(m200_main)

                # value of redshift at the current timestep 
                z_val = red_all[i]

                zre = 4.0
                        
                # time in gyr
                t_val = t_all[i]
                
            
                #round each value in the redhsifts list from DarkLight to 6 decimal places
                #np_round_to_4 = np.round(np.array(abs(t)), 7)

                idrz = np.argmin(abs(t - t_val))

                idrz_previous = np.argmin(abs(t - t_all[i-1])) if idrz>0 else None 

                msn = mstar_s_insitu[idrz]              
                
                #get the index at which the redshift of the snapshot is stored in the DarkLight array
                '''
                if idrz == 9999:
                    idrz =np.argmin(abs(t-t_val))
                else:
                    idrz+=1
                print('value of idrz ------>', idrz)
                '''
                
                if msn != 0:
                    if idrz_previous==None:
                        msp = 0
                    elif idrz_previous >= 0:
                        msp = mstar_s_insitu[idrz_previous]
                else:
                    print('There is no stellar mass at current timestep')
                    continue

                                                                                  
                
                #UNDEFINED_insitu = -9999
           
                # Using the index obtained in idrz get the value of mstar_insitu at this redshift
            
                msn = mstar_s_insitu[idrz]

                #if len(idrz)>0 else []
            
                #for the given path,entry,snapshot at given index generate a string that includes them

                #simfn = join(pynbody_path,DMOname,snapshots[i])
                #print(simfn)
                # getting the previous and current stellar mass (msp = previous, msn = now)

                 
                #if len(msn)!=0:
                
                
                    
                print('stellar masses:',msn,msp)

                #calculate the difference in mass between the two mstar's
                mass_select = int(msn-msp)
                #if le(msn)>0 else 0

                if mass_select>0:
                    decision=True
                    # try to load in the data from this snapshot
                    try:
                        simfn = join(pynbody_path,DMOname,snapshots[i])
                        print(simfn)
                        print('loading in DMO particles')
                        DMOparticles = pynbody.load(simfn)
                        # once the data from the snapshot has been loaded, .physical_units()
                        # converts all array’s units to be consistent with the distance, velocity, mass basis units specified.
                        DMOparticles.physical_units()
                        #print('total energy  ---------------------------------------------------->',DMOparticles['te'])
                        print('loaded data insitu')
                    
                    # where this data isn't available, notify the user.
                    except:
                        print('--> DMO particle data exists but failed to read it, skipping!')
                        continue
           
                    print('mass_select:',mass_select)
                    #print('total energy  ---------------------------------------------------->',DMOparticles.loadable_keys())
                    iout = np.where(outputs==snapshots[i])[0][0]
                    try:
                        hDMO['r200c']
                    except:
                        print("Couldn't load in the R200 at timestep:" , i)
                        continue
                    print('the time is:',t_all[i])
                    #h = DMOparticles.halos()[int(halonums[iout])-1]
                    #pynbody.analysis.halo.center(h)
                    #print(rank_order_particles_by_te(z_val, DMOparticles, hDMO, 'insitu'))
                    #pynbody.config["halo-class-priority"] = [pynbody.halo.ahf.AHFCatalogue]
                    
                    subhalo_iords = np.array([])
                    
                    if AHF_centers_supplied==False:
                        h = DMOparticles.halos()[int(halonums[iout])-1]

                    elif AHF_centers_supplied == True:
                        pynbody.config["halo-class-priority"] = [pynbody.halo.ahf.AHFCatalogue]
                        
                        AHF_crossref = AHF_centers[AHF_centers['i'] == i]['AHF catalogue id'].values[0]
                        
                        h = DMOparticles.halos()[int(AHF_crossref)] 
                            
                        children_ahf = AHF_centers[AHF_centers['i'] == i]['children'].values[0]
                        
                        child_str_l = children_ahf[0][1:-1].split()

                        children_ahf_int = list(map(float, child_str_l))
                        
                        #pynbody.analysis.halo.center(h)
                        
                        #pynbody.config["halo-class-priority"] = [pynbody.halo.hop.HOPCatalogue]
                    
                    
                        halo_catalogue = DMOparticles.halos()
                    
                        subhalo_iords = np.array([])
                        
                        for i in children_ahf_int:
                            
                            subhalo_iords = np.append(subhalo_iords,halo_catalogue[int(i)].dm['iord'])
                        

                        c = 0                  
                        
                                                                                                                                                
                        h = h[np.logical_not(np.isin(h['iord'],subhalo_iords))] if len(subhalo_iords) >0 else h
                    

                    pynbody.analysis.halo.center(h)

                    #pynbody.config["halo-class-priority"] = [pynbody.halo.hop.HOPCatalogue]
                                                                                                                                                                                                                   
                    try:                                                                                                                                                                                              
                        r200c_pyn = pynbody.analysis.halo.virial_radius(h.d, overden=200, r_max=None, rho_def='critical')                                                                                             
                                                                                                                                                                                                                      
                    except:                                                                                                                                                                                           
                        print('could not calculate R200c')                                                                                                                                                            
                        continue                                                                                                                                                                                      
                                                                                                                                                                                    

                    pynbody.config["halo-class-priority"] = [pynbody.halo.hop.HOPCatalogue]
                    
                    DMOparticles = DMOparticles[sqrt(DMOparticles['pos'][:,0]**2 + DMOparticles['pos'][:,1]**2 + DMOparticles['pos'][:,2]**2) <= r200c_pyn ] #hDMO['r200c']]
                    #print('angular_momentum: ', DMOparticles["j"])
                    
                    DMOparticles_insitu_only = DMOparticles[np.logical_not(np.isin(DMOparticles['iord'],subhalo_iords))]
                    
                    particles_sorted_by_te = rank_order_particles_by_te(z_val, DMOparticles_insitu_only, hDMO, centering=False)
                    
                    if particles_sorted_by_te.shape[0] == 0:
                        continue
                    
                    selected_particles,array_to_write = assign_stars_to_particles(mass_select,particles_sorted_by_te,float(fmb_percentage),selected_particles)
                    #halonums_indexing+=1
                    writer = csv.writer(particle_storage_file)
                    print('writing insitu particles to output file')
                    
                    for particle_ids,stellar_masses in zip(array_to_write[0],array_to_write[1]):
                        writer.writerow([particle_ids,stellar_masses,t_all[i],red_all[i],'insitu'])
                    print('insitu selection done')
                    
                    #pynbody.analysis.halo.center(h,mode='hyb').revert()
            
                    #print('moving onto mergers loop')
                    #get mergers ----------------------------------------------------------------------------------------------------------------
                    # check whether current the snapshot has a the redshift just before the merger occurs.
                    
                if (((i+1<len(red_all)) and (red_all[i+1] in z_set_vals)) and (mergers == True)):
                        
                    decision2 = False if decision==True else True

                    decl=False
                    
                    t_id = int(np.where(z_set_vals==red_all[i+1])[0][0])

                    if (t_all[i] > 4):
                        print('reionization -------------------------------------------<<<<<<<<<<<<<<<--------------------------------')
                
                    #print('chosen merger particles ----------------------------------------------',len(chosen_merger_particles))
                    #loop over the merging halos and collect particles from each of them
                
                    #mstars_total_darklight = np.array([])
                    DMO_particles = 0 
                    
                    for hDM in hmerge_added[t_id][0]:
                        gc.collect()
                        print('halo:',hDM)
                    
                        if (occupation_fraction != 'all'):
                            try:
                                prob_occupied = calculate_poccupied(hDM,occupation_fraction)

                            except Exception as e:
                                print(e)
                                print("poccupied couldn't be calculated")
                                continue
                            
                            if (np.random.random() > prob_occupied):
                                print('Skipped')
                                continue
                        
                        try:
                            t_2,redshift_2,vsmooth_2,sfh_in2,mstar_in2,mstar_merging = DarkLight(hDM,DMO=True,poccupied=occupation_fraction,mergers=True)
                            print(len(t_2))
                            print(mstar_merging)
                        except Exception as e :
                            print(e)
                            print('there are no darklight stars')
                            #mstars_total_darklight = np.append(mstars_total_darklight,0.0)
                        
                            continue
                
                
                        if len(mstar_merging)==0:
                            #mstars_total_darklight = np.append(mstars_total_darklight,0.0)
                            continue

                        mass_select_merge= mstar_merging[-1]
                        #mstars_total_darklight = np.append(mstars_total_darklight,mass_select_merge)

                        print(mass_select_merge)
                        if int(mass_select_merge)<1:
                            leftover+=mstar_merging[-1]
                            continue
                        
                        simfn = join(pynbody_path,DMOname,snapshots[i])

                        if float(mass_select_merge) >0 and decision2==True:
                            # try to load in the data from this snapshot
                            try:
                                DMOparticles = pynbody.load(simfn)
                                DMOparticles.physical_units()
                                print('loaded data in mergers')
                            # where this data isn't available, notify the user.
                            except:
                                print('--> DMO particle data exists but failed to read it, skipping!')
                                continue
                            decision2 = False
                            decl=True

                            try:
                                h_merge = DMOparticles.halos()[int(hDM.calculate('halo_number()'))-1]
                                pynbody.analysis.halo.center(h_merge,mode='hyb')
                                
                            except:
                                print('centering data unavailable, skipping')
                                continue
                
                        if int(mass_select_merge) > 0:
                        
                            print('mass_select:',mass_select_merge)
                            #print('total energy  ---------------------------------------------------->',DMOparticles.loadable_keys())
                            print('sorting accreted particles by TE')
                            #print(rank_order_particles_by_te(z_val, DMOparticles, hDM,'accreted'), 'output')
                            
                                                    
                            try:
                                accreted_particles_sorted_by_te = rank_order_particles_by_te(red_all[i], DMOparticles, hDM, centering=False)
                            except:
                                continue
                            
                            #print(rank_order_particles_by_te(red_all[i], DMOparticles, hDM , centering=True))
                            
                            print('assinging stars to accreted particles')
                            selected_particles,array_to_write_accreted = assign_stars_to_particles(mass_select_merge,accreted_particles_sorted_by_te,float(fmb_percentage),selected_particles)

                            
                            writer = csv.writer(particle_storage_file)
                
                        
                            print('writing accreted particles to output file')
                            #pynbody.analysis.halo.center(h_merge,mode='hyb').revert()
                             
                            for particle_ids,stellar_masses in zip(array_to_write_accreted[0],array_to_write_accreted[1]):
                                writer.writerow([particle_ids,stellar_masses,t_all[i],red_all[i],'accreted'])

                            #pynbody.analysis.halo.center(h_merge,mode='hyb').revert()
                
                    #mstars_total_darklight_l.append(mstars_total_darklight)
                            
                                    
                if decision==True or decl==True:
                    del DMOparticles
            
            
                print("Done with iteration",i)
                
    return pd.read_csv(particle_storage_filename)


def calc_3D_cm(particles,masses):
    
    x_cm = sum(particles['x']*masses)/sum(masses)
        
    y_cm = sum(particles['y']*masses)/sum(masses)
    
    z_cm = sum(particles['z']*masses)/sum(masses)

    return np.asarray([x_cm,y_cm,z_cm])


def center_on_tagged(radial_dists,mass):
    masses = np.asarray(mass)
        
    return sum(radial_dists*masses)/sum(masses)




def calculate_reffs(sim_name, particles_tagged,reffs_fname,AHF_centers_file=None,from_file = False,from_dataframe=False,save_to_file=True,AHF_centers_supplied=False):
    #used paths
    tangos_path_edge     = '/vol/ph/astro_data/shared/morkney/EDGE/tangos/'
    tangos_path_chimera  = '/vol/ph/astro_data/shared/etaylor/CHIMERA/'
    pynbody_path_edge    = '/vol/ph/astro_data/shared/morkney/EDGE/'
    pynbody_path_chimera = '/vol/ph/astro_data/shared/etaylor/CHIMERA/'
    pynbody_edge_gm =  '/vol/ph/astro_data2/shared/morkney/EDGE_GM/'

    '''

    'Halo383_fiducial'
    'Halo383_fiducial_late', 'Halo383_fiducial_288', 'Halo383_fiducial_early','Halo383_Massive',
    'Halo600_fiducial','Halo600_fiducial_later_mergers','Halo605_fiducial','Halo624_fiducial',
    'Halo624_fiducial_higher_finalmass','Halo1445_fiducial','Halo1445_fiducial','Halo1459_fiducial_Mreionx02', 'Halo1459_fiducial_Mreionx03','Halo1459_fiducial_Mreionx12','Halo600_RT', 'Halo605_RT', 'Halo624_RT',
    'Halo1445_RT','Halo1459_RT'

    '''
    pynbody.config["halo-class-priority"] = [pynbody.halo.hop.HOPCatalogue]
                    

    sims = [str(sim_name)]

    for isim,simname in enumerate(sims):

        print('==================================================')
        print(simname)
        
        # assign it a short name
        split = simname.split('_')
        shortname = split[0][4:]
        halonum = shortname[:]
        if len(split) > 2:
            if   halonum=='332': shortname += 'low'
            elif halonum=='383': shortname += 'late'
            elif halonum=='600': shortname += 'lm'
            elif halonum=='624': shortname += 'hm'
            elif halonum=='1459' and split[-1][-2:] == '02': shortname += 'mr02'
            elif halonum=='1459' and split[-1][-2:] == '03': shortname += 'mr03'
            elif halonum=='1459' and split[-1][-2:] == '12': shortname += 'mr12'
            else:
                print('unsupported simulation',simname,'! Not sure what shortname to give it. Aborting...')
                continue
        elif len(split)==2 and simname[-3:] == '_RT':  shortname += 'RT'
       # DMOname = 'Halo'+halonum+'_DMO' if split[-1]=='fiducial' else None
        #DMOname = 'Halo'+halonum+'_DMO' + ('' if len(split)==2 else ('_' +  '_'.join(split[2:])))

        if simname[-3] == 'x':
            DMOname = 'Halo'+halonum+'_DMO_'+'Mreion'+simname[-3:]

        else:
            DMOname = 'Halo'+halonum+'_DMO' + ('' if len(split)==2 else ('_' +  '_'.join(split[2:]))) #if split[1]=='fiducial' else None

                        
        # set the correct paths to data files
        if halonum == '383':
            tangos_path  = tangos_path_chimera
            pynbody_path = pynbody_path_chimera #if halonum == shortname else pynbody_edge_gm
        else:
            tangos_path  = tangos_path_edge
            pynbody_path = pynbody_path_edge if halonum == shortname else pynbody_edge_gm
        
        # get particle data at z=0 for DMO sims, if available
        if DMOname==None:
            print('--> DMO particle does not data exists, skipping!')
            continue
        # listdir returns the list of entries in a given dir path (like ls on a dir)
        # isdir check if the given dir exists
        # join creates a string consisting of the path,name,entry in dir
        # once we have this string we check to see if the word 'output' is in this string (to grab only the output snapshots)
        DMOsim = darklight.edge.load_tangos_data(DMOname)
        main_halo = DMOsim.timesteps[-1].halos[0]
        halonums = main_halo.calculate_for_progenitors('halo_number()')[0][::-1]
        outputs = np.array([DMOsim.timesteps[i].__dict__['extension'] for i in range(len(DMOsim.timesteps))])[-len(halonums):]

        print(outputs)
        
        snapshots = [ f for f in listdir(pynbody_path+DMOname) if (isdir(join(pynbody_path,DMOname,f)) and f[:6]=='output') ]
        
        #sort the list of snapshots in ascending order

        snapshots.sort()

        
        red_all = np.array([DMOsim.timesteps[i].__dict__['redshift'] for i in range(len(DMOsim.timesteps)) ])
        t_all = np.array([DMOsim.timesteps[i].__dict__['time_gyr'] for i in range(len(DMOsim.timesteps)) ])

        #load in the two files containing the particle data

        data_particles = pd.read_csv(particles_tagged)

        #print('data parts',data_particles['t'])

        data_t = np.asarray(data_particles['t'].values)
        
        stored_reff = np.array([])
        stored_reff_acc = np.array([])
        stored_reff_z = np.array([])
        stored_time = np.array([])
        kravtsov_r = np.array([])
        stored_reff_tot = np.array([])
        KE_energy = np.array([])
        PE_energy = np.array([])

        AHF_centers = pd.read_csv(str(AHF_centers_file)) if AHF_centers_supplied == True else None
                
        for i in range(len(snapshots)):

            gc.collect()

            #print(data_t[i])

            #if i >= int(stop_run):
             #   print('skipped')
              #  continue
            
            if len(np.where(data_t <= float(t_all[i]))) == 0:
                continue

            
            selected_iords_tot = np.unique(data_particles['iords'][data_particles['t']<=t_all[i]].values)
        
            #selected_iords_insitu = np.unique(data_particles['iords'][data_particles['type']=='insitu'][data_particles['t']<=t_all[i]].values)
            
            #selected_iords_acc = np.unique(data_particles['iords'][data_particles['type']=='accreted'][data_particles['t']<=t_all[i]].values)

            if selected_iords_tot.shape[0]==0:
                continue
            
            mstars_at_current_time = data_particles[data_particles['t'] <= t_all[i]].groupby(['iords']).last()['mstar']
            
            half_mass = float(mstars_at_current_time.sum())/2
            
            print(half_mass)
            #selected_iords_acc = np.array(data_particles['iords'][data_particles['z']>=red_all[i]][ data_particles['type']=='accreted'])
            #get the main halo object at the given timestep if its not available then inform the user.

            if len(DMOsim.timesteps[i].halos[:])==0:
                print('No halos!')
                continue

            elif len(np.where(outputs==snapshots[i])[0])>0 :
                
                print(np.where(outputs==snapshots[i])[0])
                
                iout = np.where(outputs==snapshots[i])[0][0]
                hDMO = tangos.get_halo(DMOname+'/'+snapshots[i]+'/halo_'+str(halonums[iout]))
                
                print(hDMO)
                
                #hDMO =DMOsim.timesteps[i].halos[0]

            else:
                print('Snap not found in outputs --------------------------------------- ')
                continue

            #for  the given path,entry,snapshot at given index generate a string that includes them
            simfn = join(pynbody_path,DMOname,snapshots[i])
            
            # try to load in the data from this snapshot
            try:  DMOparticles = pynbody.load(simfn)

            # where this data isn't available, notify the user.
            except:
                print('--> DMO particle data exists but failed to read it, skipping!')
                continue
            
            # once the data from the snapshot has been loaded, .physical_units()
            # converts all array’s units to be consistent with the distance, velocity, mass basis units specified.
            DMOparticles.physical_units()

            

            try:
                if AHF_centers_supplied==False:
                    h = DMOparticles.halos()[int(halonums[iout])-1]
                    
                elif AHF_centers_supplied == True:
                    pynbody.config["halo-class-priority"] = [pynbody.halo.ahf.AHFCatalogue]
                    
                    
                    AHF_crossref = AHF_centers[AHF_centers['i'] == i]['AHF catalogue id'].values[0]
                        
                    h = DMOparticles.halos()[int(AHF_crossref)] 
                            
                    children_ahf = AHF_centers[AHF_centers['i'] == i]['children'].values[0]
                            
                    child_str_l = children_ahf[0][1:-1].split()

                    children_ahf_int = list(map(float, child_str_l))

                        
                    #pynbody.analysis.halo.center(h)
                        
                    #pynbody.config["halo-class-priority"] = [pynbody.halo.hop.HOPCatalogue]
                    
                    
                    halo_catalogue = DMOparticles.halos()
                    
                    subhalo_iords = np.array([])
                        
                    for i in children_ahf_int:
                                
                        subhalo_iords = np.append(subhalo_iords,halo_catalogue[int(i)].dm['iord'])
                                                                                                                                                 
                    h = h[np.logical_not(np.isin(h['iord'],subhalo_iords))] if len(subhalo_iords) >0 else h
                    

                    
                pynbody.analysis.halo.center(h)
                #pynbody.config["halo-class-priority"] = [pynbody.halo.hop.HOPCatalogue]

            except:
                print('centering data unavailable')
                continue


            try:
                r200c_pyn = pynbody.analysis.halo.virial_radius(h.d, overden=200, r_max=None, rho_def='critical')

            except:
                print('could not calculate R200c')
                continue
            DMOparticles = DMOparticles[sqrt(DMOparticles['pos'][:,0]**2 + DMOparticles['pos'][:,1]**2 + DMOparticles['pos'][:,2]**2) <= r200c_pyn ]
            #pynbody.config["halo-class-priority"] = [pynbody.halo.hop.HOPCatalogue]
            
            '''                                                                    
            try:
                #DMOparticles['pos']-= hDMO['shrink_center']
                h = DMOparticles.halos()[int(halonums[iout])-1]
                pynbody.analysis.halo.center(h,mode='hyb')
                                        
            except:
                print('Tangos shrink center unavailable!')
                continue
            '''


            
            particle_selection_reff_tot = DMOparticles[np.isin(DMOparticles['iord'],selected_iords_tot)] if len(selected_iords_tot)>0 else []

            print('m200 value---->',hDMO['M200c'])

            
            
            if (len(particle_selection_reff_tot))==0:
                print('skipped!')
                continue
            else:
                
                dfnew = data_particles[data_particles['t']<=t_all[i]].groupby(['iords']).last()
                
                masses = [dfnew.loc[n]['mstar'] for n in particle_selection_reff_tot['iord']]
                
                particle_selection_reff_tot['pos'] -= calc_3D_cm(particle_selection_reff_tot,masses)
                
                distances =  np.sqrt(particle_selection_reff_tot['x']**2 + particle_selection_reff_tot['y']**2)
                #caculate the center of mass using all the tagged particles
                #cen_of_mass = center_on_tagged(distances,masses)
                
                                
                idxs_distances_sorted = np.argsort(distances)

                sorted_distances = np.sort(distances)

                distance_ordered_iords = np.asarray(particle_selection_reff_tot['iord'][idxs_distances_sorted])
                
                print('array lengths',len(set(distance_ordered_iords)),len(distance_ordered_iords))

                sorted_massess = [dfnew.loc[n]['mstar'] for n in distance_ordered_iords]
                
                cumilative_sum = np.cumsum(sorted_massess)

                R_half = sorted_distances[np.where(cumilative_sum >= (cumilative_sum[-1]/2))[0][0]]
                #print(cumilative_sum)
                
                halfmass_radius = []
                '''
                for d in range(len(sorted_distances)):
                    if cumilative_sum[d] >= half_mass:
                        halfmass_radius.append(sorted_distances[d])
                '''     

                stored_reff_z = np.append(stored_reff_z,red_all[i])
                stored_time = np.append(stored_time, t_all[i])
                   
                stored_reff = np.append(stored_reff,float(R_half))
                kravtsov = hDMO['r200c']*0.02
                kravtsov_r = np.append(kravtsov_r,kravtsov)
                particle_selection_reff_tot['pos'] += calc_3D_cm(particle_selection_reff_tot,masses)

                print('halfmass radius:',R_half)
                print('Kravtsov_radius:',kravtsov)
                
            
        #open('reffs_new23_'+halonum+'.csv','w').close()

        print('---------------------------------------------------------------writing output file --------------------------------------------------------------------')

        df_reff = pd.DataFrame({'reff':stored_reff,'z':stored_reff_z, 't':stored_time,'kravtsov':kravtsov_r})
        
        #df2_reff = pd.DataFrame({'z_tangos':ztngs, 't_tangos':ttngs,'reff_tangos':hlftngs})
        
        df_reff.to_csv(reffs_fname) if save_to_file==True else print('reffs not saved to file, to store values set save_to_file = True')
        #df2_reff.to_csv('reffs_new22_tangos'+halonum+'.csv')
        print('wrote', reffs_fname)
        
    return df_reff
