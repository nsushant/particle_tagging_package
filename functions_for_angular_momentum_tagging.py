import numpy as np 
import pandas as pd 
import darklight  
from numpy import sqrt
import random
import pynbody

def initialize_arrays(n):
    x = []
    for i in range(n):
        x.append(np.array([]))
        
    return x

def rhalf2D_dm(particles):
    #Calculate radius that encloses half the given particles.

    #Assumes each particle positions have been centered on main halo.  Adopts
    #same 'luminosity' for each particle.  Creates list of projected distances
    #from halo center (as seen from the z-axis), sorts this to get the distances
    #in increasing order, then choses the distance that encloses half the particles.

    rproj = np.sqrt(particles['x']**2 + particles['y']**2)
    rproj.sort()
    if round(len(particles)/2)>0:
        return rproj[ round(len(particles)/2) ]
    else:
        return rproj
                    
def get_dist(pos):

    # calculates the magnitude of the 3D position vector given 
    # a 3D 'pos' array 

    return np.sqrt(pos[:,0]**2+pos[:,1]**2+pos[:,2]**2)

def get_mass(m,a,r1,r2):

    # calculates the mass enclosed at distances r1 and r2 
    # from the center of the main halo 
    # according to the plummer profile 

    x1 = m*(r1**3)/((r1**2+a**2)**(3.0/2.0))
    x2 = m*(r2**3)/((r2**2+a**2)**(3.0/2.0))
    return x2-x1


def get_the_right_halonums(DMOname,halo):
    
    if DMOname=='void_volume':

        DMOsim = darklight.edge.load_tangos_data('void_volume',machine='astro')
        halo_catalog = DMOsim.timesteps[-1].halos
        main_halo = halo_catalog[int(halo) - 1]
        print(main_halo.calculate('halo_number()'),main_halo)
        halonums = main_halo.calculate_for_progenitors('halo_number()')[0][::-1]
        print(halonums)
        outputs = np.array([DMOsim.timesteps[i].__dict__['extension'] for i in range(len(DMOsim.timesteps))])[-len(halonums):]
        print(outputs)

        return DMOsim, main_halo, halonums, outputs

    else: 
        DMOsim = darklight.edge.load_tangos_data(DMOname,machine='astro')
        main_halo = DMOsim.timesteps[-1].halos[0]
        halonums = main_halo.calculate_for_progenitors('halo_number()')[0][::-1]
        outputs = np.array([DMOsim.timesteps[i].__dict__['extension'] for i in range(len(DMOsim.timesteps))])[-len(halonums):]
        #snapshots = [ f for f in listdir(pynbody_path+DMOname) if (isdir(join(pynbody_path,DMOname,f)) and f[:6]=='output') ]
        return DMOsim, main_halo, halonums, outputs




def calculate_poccupied(halo_object,occupation_regime):

    # units = kpc^3 M_sun^-1 s^-2
    G_constant = 4.3009*(10**(-6))

    # units = kpc s^-1 
    vmax = max(np.sqrt( G_constant * (halo_object['dm_mass_profile']/halo_object['rbins_profile']) ))
    
    p_occupied = darklight.core.occupation_fraction(vmax,method=occupation_regime)

    return p_occupied

    
def group_mergers(z_merges,h_merges):

    
    hmerge_added = []
    z_unique_values = sorted(list(set(z_merges)))
    
    for i in z_unique_values:
        id_hmerge_added = np.where(z_merges==i)
        x=[]
        
        for c in id_hmerge_added:
            r=np.array([])
            
            for i in c:
                r=np.append(r,h_merges[i][1:])

            x.append(r)
        
        hmerge_added.append(x)
    
    return hmerge_added, z_unique_values





def plum_const(hDMO,z_val,insitu):
    if insitu == 'insitu':
        return ((0.015*hDMO['r200c'])/1.3) if z_val > 4 else ((10**(0.1*hDMO['r200c'] - 4.2))/1.3)
    else:
        return ((0.015*hDMO['r200c'])/1.3)


#prod_binned


def rank_order_particles_by_te(z_val, DMOparticles, hDMO, centering=True):
    
    print('this is how many',len(DMOparticles))
    
    print('r200',hDMO['r200c'])
    # filter out particles outside the plummer tidal radius 'a'.
    #particles_in_selection_radius = DMOparticles[sqrt(DMOparticles['pos'][:,0]**2 + DMOparticles['pos'][:,1]**2 + DMOparticles['pos'][:,2]**2) <= 10*a ]
    
    #particles_in_twice_r200 =  DMOparticles[sqrt(DMOparticles['pos'][:,0]**2 + DMOparticles['pos'][:,1]**2 + DMOparticles['pos'][:,2]**2) <= 2*hDMO['r200c'] ]
    #particles_in_twice_r200['vel']-= particles_in_twice_r200['vel'].mean(axis=0)

    particles_in_r200 = DMOparticles[sqrt(DMOparticles['pos'][:,0]**2 + DMOparticles['pos'][:,1]**2 + DMOparticles['pos'][:,2]**2) <= hDMO['r200c']]
    
    #particles_in_selection_radius = particles_in_r200[sqrt(particles_in_r200['pos'][:,0]**2 + particles_in_r200['pos'][:,1]**2 + particles_in_r200['pos'][:,2]**2) <= 10*a] 
    #the line below is the correct form 
    #particles_in_selection_radius = particles_in_r200[sqrt(particles_in_r200['pos'][:,0]**2 + particles_in_r200['pos'][:,1]**2 + particles_in_r200['pos'][:,2]**2) <= 10*a ]
    #calculated_potential = [pynbody.analysis.gravity.potential(particles_in_r200,particle,eps=min(get_dist(particles_in_r200['pos']))/100,unit='G Msol kpc**-1') for particle in particles_in_selection_radius['pos']]
    softening_length = pynbody.array.SimArray(np.ones(len(particles_in_r200))*10.0, units='pc', sim=None)

    # print('units of mass and radius ------------>',hDMO['M200c'],hDMO['r200c'])
    
    #virial_vel = G*hDMO['M200c']/hDMO['r200c']
    
    #print('calculating potential')
    
    #calculated_potential = pynbody.analysis.gravity.potential(particles_in_r200,particles_in_selection_radius['pos'],eps=softening_length,unit='G Msol kpc**-1')

    #print('particles in selection radius:',particles_in_selection_radius['pos'].shape)
    
    #calculated_potential, calculated_force = pynbody.gravity.calc.direct(particles_in_r200,np.asarray(particles_in_r200['pos']),eps=softening_length)
    #print('potential calculated!')
    

    #kinetic_energy = particles_in_r200['ke']
    #KINETIC_E =  particles_in_selection_radius['ke']
    #calculated_potential = calculated_potential.in_units(str(kinetic_energy.units))
    
    total_energy = get_dist(particles_in_r200['j'])
    #np.asarray(kinetic_energy)+np.asarray(calculated_potential)

    #virial_test = ((2*kinetic_energy/abs(2*kinetic_energy))*np.log10(abs(2*kinetic_energy)))-((calculated_potential/abs(calculated_potential))*np.log10(np.asarray(abs(calculated_potential)))) 
    
    #if len(kinetic_energy)==0:
       # print('kinetic energy array has no elements -------------> we had ',len(particles_in_r200),'particles')
     #   kinetic_energy_avg = 0
        #print(kinetic_energy)
      #  potential_energy_avg = 0
        #print('Virial Test:',max(virial_test),min(virial_test))
        #print(kinetic_energy.units,calculated_potential.units)
        
    #else:
    #kinetic_energy_avg = kinetic_energy
    #potential_energy_avg = calculated_potential
        
    sorted_indicies = np.argsort(total_energy.flatten())
    #print('sorted_indices:',sorted_indicies.shape)
    #print("average energies:[ke,pe,z]",kinetic_energy_avg[:10],potential_energy_avg[:10],total_energy[:10],z_val)
    particles_ordered_by_te = np.asarray(particles_in_r200['iord'])[sorted_indicies] if sorted_indicies.shape[0] != 0 else np.array([]) 

    print(np.where(total_energy[sorted_indicies] <= 0),len(total_energy))
    #print(total_energy[sorted_indicies][:10])
    
    #sorted_total_energies = total_energy[sorted_indicies] 

    #bound_particles = np.where(sorted_total_energies <= max(calculated_potential))
    
    #particles_sorted_by_energy = [particles_ordered_by_te[i] for i in bound_particles[0]] if len(bound_particles)>0 else [] 

    

    #particles_in_r200['vel']+=particles_in_r200['vel'].mean(axis=0)
    
    
    #print('particles sorted by TE',total_energy[sorted_indicies][10:], np.asarray(np.asarray(particles_in_r200['ke'])[sorted_indicies] +  np.asarray(calculated_potential).flatten()[sorted_indicies])[10:])
    
    virial_velocity = hDMO['M200c']/hDMO['r200c']

    print("virial velocity:", virial_velocity)

    #print('length of particle array: ' , bound_particles, max(calculated_potential))

    return np.asarray(particles_ordered_by_te)


#get bins 

def assign_stars_to_particles(snapshot_stellar_mass,particles_sorted_by_te,most_bound_fraction,selected_particles):
    
    '''
    selected_particles is a 2d array with rows = 2, cols = num of particles  
    
    selected_particles[0] = iords
    selected_particles[1] = stellar mass
    
    '''
    
    #print('number of particles sorted: ',particles_sorted_by_te)

    #print('no. of particels:', particles_sorted_by_te.shape[0])

    size_of_most_bound_fraction = int(particles_sorted_by_te.shape[0]*most_bound_fraction)
    
    particles_in_most_bound_fraction = particles_sorted_by_te[:size_of_most_bound_fraction]

    #print('sorted particles that are in the most bound fraction: ',np.where(np.isin(particles_sorted_by_te,particles_in_most_bound_fraction)==True))
    
    #dividing stellar mass evenly over all the particles in the most bound fraction 

    print('assigning stellar mass')
    
    stellar_mass_assigned = float(snapshot_stellar_mass/len(list(particles_in_most_bound_fraction))) if len(list(particles_in_most_bound_fraction))>0 else 0
    
    
    #check if particles have been selected before 
    
    idxs_previously_selected = np.where(np.isin(selected_particles[0],particles_in_most_bound_fraction)==True)

    #print('indicies of particles selected in previous snap that are still in fmb:',np.where(np.isin(particles_in_most_bound_fraction,selected_particles[0])==True))
    
    selected_particles[1] = np.where(np.isin(selected_particles[0],particles_in_most_bound_fraction)==True,selected_particles[1]+stellar_mass_assigned,selected_particles[1]) 

    #[idxs_previously_selected] += stellar_mass_assigned
    
    #if not selected previously, add to array
    
    idxs_not_previously_selected = np.where(np.isin(particles_in_most_bound_fraction,selected_particles[0])==False)

    how_many_not_previously_selected = particles_in_most_bound_fraction[idxs_not_previously_selected].shape[0]
    
    selected_particles_new_iords = np.append(selected_particles[0],particles_in_most_bound_fraction[idxs_not_previously_selected])
    
    selected_particles_new_masses = np.append(selected_particles[1],np.repeat(stellar_mass_assigned,how_many_not_previously_selected))

    #print(np.where(np.isin(particles_sorted_by_te,selected_particles[0])==True), 'selected indicies before')
    selected_particles = np.array([selected_particles_new_iords,selected_particles_new_masses])

    array_iords = np.append(selected_particles[0][idxs_previously_selected], particles_in_most_bound_fraction[idxs_not_previously_selected])

    array_masses = np.append(selected_particles[1][idxs_previously_selected],np.repeat(stellar_mass_assigned,how_many_not_previously_selected))

    updates_to_arrays = np.array([array_iords,array_masses])

    #print(np.where(np.isin(particles_sorted_by_te,selected_particles[0])==True), 'selected indicies after')

    #print(selected_particles[0].flatten().shape[0],'particles successfully tagged')

    #print(selected_particles[0])

    return selected_particles,updates_to_arrays
    

    

    
    
    
    
    
    
