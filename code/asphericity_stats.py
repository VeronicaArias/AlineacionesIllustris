import numpy as np
import glob
import os
import matplotlib.pyplot as plt
import corner

def load_summary(filename):
    dtype=[('minr', 'f8'),
           ('maxr', 'f8'), 
           ('ca_ratio', 'f8'),
           ('ba_ratio', 'f8'),
           ('a', 'f8'),
           ('center', 'f8'),
           ('width', 'f8'),
           ('mu', 'f8')]
    summary = np.loadtxt(filename, dtype=dtype)    
    return summary

def load_experiment(input_path="../data/mstar_selected_summary/vmax_sorted/", n_sat=11, full_data=False):
    files = glob.glob(input_path+"M31_group_*_nsat_{}.dat".format(n_sat))
    group_id = []
    for f in files:
        i = int(f.split("_")[-3])
        if i not in group_id:
            group_id.append(i)
    #print(group_id, len(group_id))

    n_groups = len(group_id)
    
    fields = ['width','mu', 'a', 'ba_ratio', 'ca_ratio']
    M31_all = {}
    MW_all = {}
    if full_data:
        for field in fields:
            M31_all[field] = np.empty((0))
            MW_all[field] = np.empty((0))
            M31_all[field+'_random'] = np.empty((0))
            MW_all[field+'_random'] = np.empty((0))
    else:
        for field in fields:
            M31_all[field] = np.ones(n_groups)
            MW_all[field] = np.ones(n_groups)
            M31_all[field+'_sigma'] = np.ones(n_groups)
            MW_all[field+'_sigma'] = np.ones(n_groups)
        
            M31_all[field+'_random'] = np.ones(n_groups)
            MW_all[field+'_random'] = np.ones(n_groups)
            M31_all[field+'_random_sigma'] = np.ones(n_groups)
            MW_all[field+'_random_sigma'] = np.ones(n_groups)
            M31_all[field+'_normed'] = np.ones(n_groups)
            MW_all[field+'_normed'] = np.ones(n_groups)

    MW_summary = {}
    M31_summary = {}
    for g in range(n_groups):
        filename_MW = os.path.join(input_path,"MW_group_{}_nsat_{}.dat".format(group_id[g],n_sat))
        filename_M31 = os.path.join(input_path,"M31_group_{}_nsat_{}.dat".format(group_id[g],n_sat))

        MW_summary[g] = load_summary(filename_MW)
        M31_summary[g] = load_summary(filename_M31)
    
    
    for field in fields:
        a = np.empty((0))
        b = np.empty((0))
        a_random = np.empty((0))
        b_random = np.empty((0))
        
        for g in range(n_groups):
            data = M31_summary[g]
            a = data[field][0]
            a_random = data[field][1:]
        
            data = MW_summary[g]
            b = data[field][0]
            b_random = data[field][1:]
                #print('a_random {} iter: {} {}'.format(field, i, a_random))
           
            if full_data:
                M31_all[field] = np.append(M31_all[field], a)
                MW_all[field] = np.append(MW_all[field], b)
                M31_all[field+'_random'] = np.append(M31_all[field+'_random'], a_random)
                MW_all[field+'_random'] = np.append(MW_all[field+'_random'], b_random)
        
            else:
                M31_all[field][g] = np.average(a)
                MW_all[field][g] = np.average(b)
                M31_all[field+'_sigma'][g] = np.std(a)
                MW_all[field+'_sigma'][g] = np.std(b)
                M31_all[field+'_random'][g] = np.average(a_random)
                MW_all[field+'_random'][g] = np.average(b_random)
                M31_all[field+'_random_sigma'][g] = np.std(a_random)
                MW_all[field+'_random_sigma'][g] = np.std(b_random)
                M31_all[field+'_normed'][g] = (M31_all[field][g] - M31_all[field+'_random'][g])/M31_all[field+'_random_sigma'][g]
                MW_all[field+'_normed'][g] = (MW_all[field][g] - MW_all[field+'_random'][g])/MW_all[field+'_random_sigma'][g]
                
    return M31_all, MW_all

def points_in_experiment(experiment):
    keys = list(experiment.keys())
    n_points = len(experiment[keys[0]])
    return n_points

def copy_experiment(experiment, id_to_remove=None):
    copy = {}
    n_points = points_in_experiment(experiment)
    for k in experiment.keys():
        if id_to_remove is None:
            copy[k] = experiment[k].copy()
        else:
            ii = np.arange(n_points)
            copy[k] = experiment[k][ii!=id_to_remove]
    return copy

def get_data_obs(obs_data, normed=True):
    fields = {0:'width', 1:'ca_ratio', 2:'ba_ratio'}
    n_fields = len(fields)
    data_obs = np.zeros((n_fields, len(obs_data['width'])))

    for i in range(n_fields):
        field = fields[i]
        if normed:
            x_obs = (obs_data[field] - obs_data[field+'_random'])/obs_data[field+'_random_sigma']
        else:
            x_obs = obs_data[field]
        data_obs[i,:] = x_obs[:]
    
    return {'data_obs': data_obs, 'fields':fields}


def covariance_and_mean(experiment):
    fields = {0:'width', 1:'ca_ratio', 2:'ba_ratio'}
    n_fields = len(fields)
    n_points = points_in_experiment(experiment)
    data_sim = np.zeros((n_fields, n_points))
    for i in range(n_fields):
        field = fields[i]
        x_sim = (experiment[field] - experiment[field+'_random'])/experiment[field+'_random_sigma']
        data_sim[i,:] = x_sim[:]
    
    data_cov = np.cov(data_sim)
    data_mean = np.mean(data_sim, axis=1)

    return {'covariance':data_cov, 'mean':data_mean, 'fields':fields}


def jacknife_covariance(experiment):
    cov_and_mean = {}
    n_points = points_in_experiment(experiment)
    for i in range(n_points):
        tmp = copy_experiment(experiment, id_to_remove=i)
        cov_and_mean[i] = covariance_and_mean(tmp)
        
    covariance_avg = cov_and_mean[0]['covariance'] - cov_and_mean[0]['covariance']
    for i in range(n_points):
        covariance_avg += cov_and_mean[i]['covariance']
    covariance_avg = covariance_avg/n_points

    covariance_std = cov_and_mean[0]['covariance'] - cov_and_mean[0]['covariance']
    for i in range(n_points):
        covariance_std += (cov_and_mean[i]['covariance']-covariance_avg)**2
    covariance_std = np.sqrt(covariance_std/n_points)
    
    mean_avg = cov_and_mean[0]['mean'] - cov_and_mean[0]['mean']
    for i in range(n_points):
        mean_avg += cov_and_mean[i]['mean']
    mean_avg = mean_avg/n_points

    mean_std = cov_and_mean[0]['mean'] - cov_and_mean[0]['mean']
    for i in range(n_points):
        mean_std += (cov_and_mean[i]['mean'] - mean_avg)**2
    mean_std = np.sqrt(mean_std/20)
    
    
    return {'covariance': covariance_avg, 'covariance_error': covariance_std, 'mean': mean_avg, 'mean_error': mean_std}


def print_table_obs_shape():
    fields = ['width','ca_ratio', 'ba_ratio']
    names = {'width':'Plane width (kpc)', 'ca_ratio':'$c/a$ ratio', 'ba_ratio':'$b/a$ ratio'}

    for n_sat in range(11,16):
        print("OBSERVATIONS - NSAT = {}".format(n_sat))
        in_path = "../data/obs_summary/"
        M31_obs_stats, MW_obs_stats = load_experiment(input_path=in_path, n_sat=n_sat, full_data=False)

        print("M31(phys) - MW(phys) | M31(rand) | MW (rand) | M31(norm) | MW (norm)|")
        for field in fields:
            print("{} & ${:.2f}$ & ${:.2f}$ & ${:.2f}\pm{:.2f}$ & ${:.2f}\pm{:.2f}$ & ${:.2f}$ & ${:.2f}$\\\\\\hline".format(
                names[field], 
                M31_obs_stats[field][0], MW_obs_stats[field][0],
                M31_obs_stats[field+'_random'][0], M31_obs_stats[field+'_random_sigma'][0],
                MW_obs_stats[field+'_random'][0],MW_obs_stats[field+'_random_sigma'][0],
                (M31_obs_stats[field][0]-M31_obs_stats[field+'_random'][0])/M31_obs_stats[field+'_random_sigma'][0],
                (MW_obs_stats[field][0]-MW_obs_stats[field+'_random'][0])/MW_obs_stats[field+'_random_sigma'][0]))
        print()

def print_table_sim_shape():
    fields = ['width','ca_ratio', 'ba_ratio']
    names = {'width':'Plane width (kpc)', 'ca_ratio':'$c/a$ ratio', 'ba_ratio':'$b/a$ ratio'}
    for n_sat in range(11,16):
        print("IllustrisDark / Illustris / Elvis - NSAT = {}".format(n_sat))
        in_path = "../data/illustris1_mstar_selected_summary/"
        M31_illu_stats, MW_illu_stats = load_experiment(input_path=in_path, n_sat=n_sat)
        in_path = "../data/illustris1dark_mstar_selected_summary/"
        M31_illudark_stats, MW_illudark_stats = load_experiment(input_path=in_path, n_sat=n_sat)
        in_path = "../data/elvis_mstar_selected_summary/"
        M31_elvis_stats, MW_elvis_stats = load_experiment(input_path=in_path, n_sat=n_sat)

        print("M31(phys) - MW(phys)|")
        for field in fields:
            print("{} & ${:.2f}\pm {:.2f}$ & ${:.2f} \pm {:.2f}$  & ${:.2f}\pm {:.2f}$ & ${:.2f}\pm {:.2f}$ & ${:.2f}\pm {:.2f}$ & ${:.2f}\pm {:.2f}$\\\\\\hline".format(
                names[field],
                np.mean(M31_illudark_stats[field]), np.std(M31_illudark_stats[field]),
                np.mean(MW_illudark_stats[field]), np.std(MW_illudark_stats[field]), 
                np.mean(M31_illu_stats[field]), np.std(M31_illu_stats[field]),
                np.mean(MW_illu_stats[field]), np.std(MW_illu_stats[field]), 
                np.mean(M31_elvis_stats[field]), np.std(M31_elvis_stats[field]),
                np.mean(MW_elvis_stats[field]), np.std(MW_elvis_stats[field])))
        print()
             
            
def plot_covariance(simulation, n_sat):
    simulation_name = {'illustris1':'Illustris1', 'illustris1dark':'Illustris1Dark', 'elvis':'ELVIS'}
    print('simulation {}'.format(simulation))
    in_path = "../data/{}_mstar_selected_summary/".format(simulation)
    M31_sim_stats, MW_sim_stats = load_experiment(input_path=in_path, n_sat=n_sat)

    
    in_path = "../data/obs_summary/"
    M31_obs_stats, MW_obs_stats = load_experiment(input_path=in_path, n_sat=n_sat, full_data=False)
    M31_obs = get_data_obs(M31_obs_stats)
    MW_obs = get_data_obs(MW_obs_stats)
    
    cov_illustris_M31 = jacknife_covariance(M31_sim_stats)
    cov_illustris_MW = jacknife_covariance(MW_sim_stats)
        
    data_random_illustris_M31 = np.random.multivariate_normal(
            cov_illustris_M31['mean'], cov_illustris_M31['covariance'], size=100000)
    data_random_illustris_MW = np.random.multivariate_normal(
            cov_illustris_MW['mean'], cov_illustris_MW['covariance'], size=100000)
    s = np.array([1.0,2.0,3.0])
    levels = 1-np.exp(-(s**2)/2.0)
        
    plt.figure(figsize=(8,5))
    plt.rc('text', usetex=True,)
    plt.rc('font', family='serif', size=25)
    figure = corner.corner( data_random_illustris_M31, 
                      quantiles=[0.16, 0.5, 0.84],levels=levels,
                      labels=[r"$w$ M31", r"$c/a$ M31", r"$b/a$ M31"],
                      show_titles=True, title_kwargs={"fontsize": 12}, 
                      truths=M31_obs['data_obs'])
        
        
    min_w = -4; max_w = 4; min_ac = -4; max_ac = 4 ; min_ab = -4; max_ab = 4
    ndim = 3
    axes = np.array(figure.axes).reshape(ndim,ndim)
    ax = axes[1,1];ax.set_xlim(min_ac, max_ac)
    ax = axes[2,1];ax.set_xlim(min_ac, max_ac);ax.set_ylim(min_ab, max_ab);
    ax.scatter(M31_sim_stats['ca_ratio_normed'], M31_sim_stats['ba_ratio_normed'])
    ax = axes[2,2];ax.set_xlim(min_ab, max_ab)
    ax = axes[0,0];ax.set_xlim(min_w, max_w)
    ax = axes[1,0];ax.set_xlim(min_w, max_w);ax.set_ylim(min_ac, max_ac)
    ax.scatter(M31_sim_stats['width_normed'], M31_sim_stats['ca_ratio_normed'])
    ax = axes[2,0];ax.set_xlim(min_w, max_w);ax.set_ylim(min_ab, max_ab)
    ax.scatter(M31_sim_stats['width_normed'], M31_sim_stats['ba_ratio_normed'])
    children = ax.get_children()
    ax.legend([children[5], children[7], children[4]], [simulation_name[simulation], 'Observations', 'Gaussian Model'], 
              loc='upper right', bbox_to_anchor=(3.0, 3.0), fontsize=20, markerscale=2)

    filename = "../paper/gaussian_model_{}_M31_n_{}.pdf".format(simulation, n_sat)
    print('saving figure to {}'.format(filename))
    plt.savefig(filename, bbox_inches='tight')
    plt.clf()
        
    plt.figure(figsize=(8,5))
    plt.rc('text', usetex=True,)
    plt.rc('font', family='serif', size=25)
    figure = corner.corner(data_random_illustris_MW, 
                      quantiles=[0.16, 0.5, 0.84],levels=levels,
                      labels=[r"$w$ MW", r"$c/a$ MW", r"$b/a$ MW"],
                      show_titles=True, title_kwargs={"fontsize": 12}, 
                      truths=MW_obs['data_obs'])
    min_w = -4; max_w = 4; min_ac = -4; max_ac = 4 ; min_ab = -4; max_ab = 4
    ndim = 3
    axes = np.array(figure.axes).reshape(ndim,ndim)
    ax = axes[1,1];ax.set_xlim(min_ac, max_ac)
    ax = axes[2,1];ax.set_xlim(min_ac, max_ac);ax.set_ylim(min_ab, max_ab);
    ax.scatter(MW_sim_stats['ca_ratio_normed'], MW_sim_stats['ba_ratio_normed'])
    ax = axes[2,2];ax.set_xlim(min_ab, max_ab)
    ax = axes[0,0];ax.set_xlim(min_w, max_w)
    ax = axes[1,0];ax.set_xlim(min_w, max_w);ax.set_ylim(min_ac, max_ac)
    ax.scatter(MW_sim_stats['width_normed'], MW_sim_stats['ca_ratio_normed'])
    ax = axes[2,0];ax.set_xlim(min_w, max_w);ax.set_ylim(min_ab, max_ab)
    ax.scatter(MW_sim_stats['width_normed'], MW_sim_stats['ba_ratio_normed'])
    children = ax.get_children()
    ax.legend([children[5], children[7], children[4]], [simulation_name[simulation], 'Observations', 'Gaussian Model'], 
              loc='upper right', bbox_to_anchor=(3.0, 3.0), fontsize=20, markerscale=2)
    filename = "../paper/gaussian_model_{}_MW_n_{}.pdf".format(simulation, n_sat)
    print('saving figure to {}'.format(filename))
    plt.savefig(filename, bbox_inches='tight')
    plt.clf()
    
    plt.close('all')


def plot_asphericity_obs(field):
    plt.figure(figsize=(7,7))
    plt.rc('text', usetex=True,)
    plt.rc('font', family='serif', size=25)
    for n_sat in range(11,16):
        in_path = "../data/obs_summary/"
        M31_obs_stats, MW_obs_stats = load_experiment(input_path=in_path, n_sat=n_sat, full_data=False)
        M31_obs = get_data_obs(M31_obs_stats)
        MW_obs = get_data_obs(MW_obs_stats)
        print(n_sat, M31_obs['fields'][field], MW_obs['fields'][field],M31_obs['data_obs'][field], MW_obs['data_obs'][field])
        if n_sat==11:
            plt.scatter(n_sat, M31_obs['data_obs'][field], marker='*', s=300, color='black', alpha=0.9, label='M31')
            plt.scatter(n_sat, MW_obs['data_obs'][field], marker='o', s=300, color='black', alpha=0.9, label='MW')
        else:
            plt.scatter(n_sat, M31_obs['data_obs'][field], marker='*', s=300, color='black', alpha=0.9)
            plt.scatter(n_sat, MW_obs['data_obs'][field], marker='o', s=300, color='black', alpha=0.9)
            
    ylabel = {'width': 'Normalized Plane Width', 'ca_ratio':'Normalized $c/a$ ratio', 'ba_ratio':'Normalized $b/a$ ratio'}
    plt.legend()
    plt.xlabel("$N_s$")
    plt.ylabel(ylabel[M31_obs['fields'][field]])
    plt.grid()
    filename = "../paper/normalized_{}_n_dependence.pdf".format(M31_obs['fields'][field])
    print('saving figure to {}'.format(filename))
    plt.savefig(filename, bbox_inches='tight')
    plt.clf()
    
def number_LG(sim_cov_M31, sim_mean_M31, sim_cov_MW, sim_mean_MW, obs_M31, obs_MW, n_sample=20):
    n_try = 1000
    n_out = np.ones(n_try)
    n_MW = np.ones(n_try)
    n_M31 = np.ones(n_try)

    for i in range(n_try):
        sim_M31 = np.random.multivariate_normal(sim_mean_M31, sim_cov_M31, size=n_sample)
        sim_MW = np.random.multivariate_normal(sim_mean_MW, sim_cov_MW, size=n_sample)
        
        like_M31_from_M31 = sim_M31[:,0]<1E6
        like_MW_from_MW = sim_MW[:,0]<1E6
        for j in range(3):
            like_M31_from_M31 &= (np.abs(sim_M31[:,j]-sim_mean_M31[j]) > np.abs(obs_M31[j]-sim_mean_M31[j]))
            like_MW_from_MW &= (np.abs(sim_MW[:,j]-sim_mean_MW[j]) > np.abs(obs_MW[j]-sim_mean_MW[j]))
        #print(sim_M31[like_M31_from_M31,:])
        
        n_out[i] = np.count_nonzero(like_M31_from_M31 & like_MW_from_MW)
        n_MW[i] = np.count_nonzero(like_MW_from_MW)
        n_M31[i] = np.count_nonzero(like_M31_from_M31)
        #print(n_M31[i])
    return {'n_LG': n_out, 'n_MW':n_MW, 'n_M31':n_M31}


def get_numbers(simulation, n_sat):
    print('simulation {}'.format(simulation))
    in_path = "../data/{}_mstar_selected_summary/".format(simulation)
    M31_sim_stats, MW_sim_stats = load_experiment(input_path=in_path, n_sat=n_sat)

    in_path = "../data/obs_summary/"
    M31_obs_stats, MW_obs_stats = load_experiment(input_path=in_path, n_sat=n_sat, full_data=False)
    M31_obs = get_data_obs(M31_obs_stats)
    MW_obs = get_data_obs(MW_obs_stats)
    
    cov_sim_M31 = jacknife_covariance(M31_sim_stats)
    cov_sim_MW = jacknife_covariance(MW_sim_stats)
            
    n_out_list_sim = number_LG(cov_sim_M31['covariance'], cov_sim_M31['mean'],
             cov_sim_MW['covariance'], cov_sim_MW['mean'],
             M31_obs['data_obs'], MW_obs['data_obs'], n_sample=10000)
    return {'mean_n_M31':np.mean(n_out_list_sim['n_M31']), 'std_n_M31':np.std(n_out_list_sim['n_M31']),
           'mean_n_MW':np.mean(n_out_list_sim['n_MW']), 'std_n_MW':np.std(n_out_list_sim['n_MW']),
           'mean_n_LG':np.mean(n_out_list_sim['n_LG']), 'std_n_LG':np.std(n_out_list_sim['n_LG'])}
    print()
    
def print_numbers():
    LG_out = open('../data/numbers/LG_numbers.txt', 'w')
    M31_out = open('../data/numbers/M31_numbers.txt', 'w')
    MW_out = open('../data/numbers/MW_numbers.txt', 'w')

    for i in range(11,16):
        a = get_numbers('illustris1dark', i)
        b = get_numbers('illustris1', i)
        c = get_numbers('elvis', i)
        LG_out.write("{} {} {} {} {} {} {}\n".format(i, 
                                                  a['mean_n_LG'], a['std_n_LG'],
                                                  b['mean_n_LG'], b['std_n_LG'],
                                                  c['mean_n_LG'], c['std_n_LG']))
        M31_out.write("{} {} {} {} {} {} {}\n".format(i, 
                                                  a['mean_n_M31'], a['std_n_M31'],
                                                  b['mean_n_M31'], b['std_n_M31'],
                                                  c['mean_n_M31'], c['std_n_M31']))
        MW_out.write("{} {} {} {} {} {} {}\n".format(i, 
                                                  a['mean_n_MW'], a['std_n_MW'],
                                                  b['mean_n_MW'], b['std_n_MW'],
                                                  c['mean_n_MW'], c['std_n_MW']))
    
    MW_out.close()
    M31_out.close()
    LG_out.close()
    
def plot_numbers():
    LG_data = np.loadtxt('../data/numbers/LG_numbers.txt')
    M31_data = np.loadtxt('../data/numbers/M31_numbers.txt')
    MW_data = np.loadtxt('../data/numbers/MW_numbers.txt')
    LG_data[:,1:] = LG_data[:,1:]/1E2
    M31_data[:,1:] = M31_data[:,1:]/1E2
    MW_data[:,1:] = MW_data[:,1:]/1E2
    plt.figure(figsize=(7,7))
    plt.rc('text', usetex=True,)
    plt.rc('font', family='serif', size=25)

    plt.errorbar(LG_data[:,0], LG_data[:,1], yerr=LG_data[:,2],
                fmt='*', markersize=20, color='black', alpha=0.5, label='Illustris1Dark')
    plt.errorbar(LG_data[:,0], LG_data[:,3], yerr=LG_data[:,4],
                fmt='o', markersize=20, color='black', alpha=0.5, label='Illustris1')
    plt.errorbar(LG_data[:,0], LG_data[:,5], yerr=LG_data[:,6],
                fmt='>', markersize=20, color='black', alpha=0.5, label='ELVIS')
    plt.legend()
    plt.xlabel("$N_s$")
    plt.ylabel("Local Group Systems $(\%)$")
    plt.grid()
    filename = "../paper/LG_numbers.pdf"
    print('saving figure to {}'.format(filename))
    plt.savefig(filename, bbox_inches='tight')
    plt.clf()
    
    plt.figure(figsize=(7,7))
    plt.rc('text', usetex=True,)
    plt.rc('font', family='serif', size=25)

    plt.errorbar(MW_data[:,0], MW_data[:,1], yerr=MW_data[:,2],
                fmt='*', markersize=20, color='black', alpha=0.5, label='Illustris1Dark')
    plt.errorbar(MW_data[:,0], MW_data[:,3], yerr=MW_data[:,4],
                fmt='o', markersize=20, color='black', alpha=0.5, label='Illustris1')
    plt.errorbar(MW_data[:,0], MW_data[:,5], yerr=MW_data[:,6],
                fmt='>', markersize=20, color='black', alpha=0.5, label='ELVIS')
    plt.xlabel("$N_s$")
    plt.ylabel("MW Galaxies $(\%)$")
    plt.grid()
    filename = "../paper/MW_numbers.pdf"
    print('saving figure to {}'.format(filename))
    plt.savefig(filename, bbox_inches='tight')
    plt.clf()
    
    plt.figure(figsize=(7,7))
    plt.rc('text', usetex=True,)
    plt.rc('font', family='serif', size=25)

    plt.errorbar(M31_data[:,0], M31_data[:,1], yerr=M31_data[:,2],
                fmt='*', markersize=20, color='black', alpha=0.5, label='Illustris1Dark')
    plt.errorbar(M31_data[:,0], M31_data[:,3], yerr=M31_data[:,4],
                fmt='o', markersize=20, color='black', alpha=0.5, label='Illustris1')
    plt.errorbar(M31_data[:,0], M31_data[:,5], yerr=M31_data[:,6],
                fmt='>', markersize=20, color='black', alpha=0.5, label='ELVIS')
    plt.xlabel("$N_s$")
    plt.ylabel("M31 Galaxies $(\%)$")
    plt.grid()
    filename = "../paper/M31_numbers.pdf"
    print('saving figure to {}'.format(filename))
    plt.savefig(filename, bbox_inches='tight')
    plt.clf()
    

def plot_shape_obs_randoms(n_sat):
    in_path = "../data/obs_summary/"
    M31_obs_stats, MW_obs_stats = load_experiment(input_path=in_path, n_sat=n_sat, full_data=False)
    M31_obs = get_data_obs(M31_obs_stats, normed=False)
    MW_obs =  get_data_obs(MW_obs_stats, normed=False)

    M31_obs_stats, MW_obs_stats = load_experiment(input_path=in_path, n_sat=n_sat, full_data=True)    
    data_random_obs_M31 = np.array([M31_obs_stats['width_random'],
                                    M31_obs_stats['ca_ratio_random'], 
                                    M31_obs_stats['ba_ratio_random']]).T
    data_random_obs_MW = np.array([MW_obs_stats['width_random'],
                                    MW_obs_stats['ca_ratio_random'], 
                                    MW_obs_stats['ba_ratio_random']]).T
    
    print(np.shape(data_random_obs_MW))
    print(MW_obs)
        
    plt.figure(figsize=(8,5))
    plt.rc('text', usetex=True,)
    plt.rc('font', family='serif', size=25)
    figure = corner.corner(data_random_obs_M31, 
                      quantiles=[0.16, 0.5, 0.84],
                      labels=[r"$w$ M31", r"$c/a$ M31", r"$b/a$ M31"],
                      show_titles=True, title_kwargs={"fontsize": 12}, 
                      truths=M31_obs['data_obs'])
        
        
    min_w = 10; max_w = 90; min_ac = 0.0; max_ac = 1.0 ; min_ab = 0.6; max_ab = 1.0
    ndim = 3
    axes = np.array(figure.axes).reshape(ndim,ndim)
    ax = axes[1,1];ax.set_xlim(min_ac, max_ac)
    ax = axes[2,1];ax.set_xlim(min_ac, max_ac);ax.set_ylim(min_ab, max_ab)
    ax = axes[2,2];ax.set_xlim(min_ab, max_ab)
    ax = axes[0,0];ax.set_xlim(min_w, max_w)
    ax = axes[1,0];ax.set_xlim(min_w, max_w);ax.set_ylim(min_ac, max_ac)
    ax = axes[2,0];ax.set_xlim(min_w, max_w);ax.set_ylim(min_ab, max_ab)


    filename = "../paper/input_obs_M31_n_{}.pdf".format(n_sat)
    print('saving figure to {}'.format(filename))
    plt.savefig(filename, bbox_inches='tight')
    plt.clf()
        
    plt.figure(figsize=(8,5))
    plt.rc('text', usetex=True,)
    plt.rc('font', family='serif', size=25)
    figure = corner.corner(data_random_obs_MW, 
                      quantiles=[0.16, 0.5, 0.84],
                      labels=[r"$w$ MW", r"$c/a$ MW", r"$b/a$ MW"],
                      show_titles=True, title_kwargs={"fontsize": 12}, 
                      truths=MW_obs['data_obs'])
    
    ndim = 3
    axes = np.array(figure.axes).reshape(ndim,ndim)
    ax = axes[1,1];ax.set_xlim(min_ac, max_ac)
    ax = axes[2,1];ax.set_xlim(min_ac, max_ac);ax.set_ylim(min_ab, max_ab)
    ax = axes[2,2];ax.set_xlim(min_ab, max_ab)
    ax = axes[0,0];ax.set_xlim(min_w, max_w)
    ax = axes[1,0];ax.set_xlim(min_w, max_w);ax.set_ylim(min_ac, max_ac)
    ax = axes[2,0];ax.set_xlim(min_w, max_w);ax.set_ylim(min_ab, max_ab)

    filename = "../paper/input_obs_MW_n_{}.pdf".format(n_sat)
    print('saving figure to {}'.format(filename))
    plt.savefig(filename, bbox_inches='tight')
    plt.clf()
    
    plt.close('all')

    
def plot_shape_obs_sims(simulation, n_sat):
    print('simulation {}'.format(simulation))
    simulation_name = {'illustris1':'Illustris1', 'illustris1dark':'Illustris1Dark', 'elvis':'ELVIS'}
    in_path = "../data/{}_mstar_selected_summary/".format(simulation)
    M31_sim_stats, MW_sim_stats = load_experiment(input_path=in_path, n_sat=n_sat, full_data=True)
    
    in_path = "../data/obs_summary/"
    M31_obs_stats, MW_obs_stats = load_experiment(input_path=in_path, n_sat=n_sat, full_data=False)
    M31_obs = get_data_obs(M31_obs_stats, normed=False)
    MW_obs =  get_data_obs(MW_obs_stats, normed=False)

    M31_obs_stats, MW_obs_stats = load_experiment(input_path=in_path, n_sat=n_sat, full_data=True)    
    data_random_obs_M31 = np.array([M31_obs_stats['width_random'],
                                    M31_obs_stats['ca_ratio_random'], 
                                    M31_obs_stats['ba_ratio_random']]).T
    data_random_obs_MW = np.array([MW_obs_stats['width_random'],
                                    MW_obs_stats['ca_ratio_random'], 
                                    MW_obs_stats['ba_ratio_random']]).T
    
    print(np.shape(data_random_obs_MW))
    print(MW_obs)
    s = np.array([1.0,2.0,3.0])
    levels = 1-np.exp(-(s**2)/2.0)
        
    plt.figure(figsize=(8,5))
    plt.rc('text', usetex=True,)
    plt.rc('font', family='serif', size=25)
    plt.title("Physical Quantities")
    figure = corner.corner(data_random_obs_M31, 
                     levels = levels,
                      quantiles=[0.16, 0.5, 0.84],
                      labels=[r"$w$ (kpc) M31", r"$c/a$ M31", r"$b/a$ M31"],
                      show_titles=True, title_kwargs={"fontsize": 12}, 
                      truths=M31_obs['data_obs'])
        
        
    min_w = 10; max_w = 90; min_ac = 0.0; max_ac = 1.0 ; min_ab = 0.6; max_ab = 1.0
    ndim = 3
    axes = np.array(figure.axes).reshape(ndim,ndim)
    ax = axes[1,1];ax.set_xlim(min_ac, max_ac)
    ax = axes[2,1];ax.set_xlim(min_ac, max_ac);ax.set_ylim(min_ab, max_ab);
    ax.scatter(M31_sim_stats['ca_ratio'], M31_sim_stats['ba_ratio'])
    ax = axes[2,2];ax.set_xlim(min_ab, max_ab)
    ax = axes[0,0];ax.set_xlim(min_w, max_w)
    ax = axes[1,0];ax.set_xlim(min_w, max_w);ax.set_ylim(min_ac, max_ac)
    ax.scatter(M31_sim_stats['width'], M31_sim_stats['ca_ratio'])
    ax = axes[2,0];ax.set_xlim(min_w, max_w);ax.set_ylim(min_ab, max_ab)
    ax.scatter(M31_sim_stats['width'], M31_sim_stats['ba_ratio'])
    children = ax.get_children()
    ax.legend([children[5], children[7], children[4]], [simulation_name[simulation], 'Observations', 'Randomized Obs.'], 
              loc='upper right', bbox_to_anchor=(3.0, 3.0), fontsize=20, markerscale=2)
    
    filename = "../paper/input_{}_obs_M31_n_{}.pdf".format(simulation, n_sat)
    print('saving figure to {}'.format(filename))
    
    plt.savefig(filename, bbox_inches='tight')
    plt.clf()
        
    plt.figure(figsize=(8,5))
    plt.rc('text', usetex=True,)
    plt.rc('font', family='serif', size=25)

    figure = corner.corner(data_random_obs_MW, 
                      quantiles=[0.16, 0.5, 0.84],
                      levels = levels,
                      labels=[r"$w$ (kpc) MW", r"$c/a$ MW", r"$b/a$ MW"],
                      show_titles=True, title_kwargs={"fontsize": 12}, 
                      truths=MW_obs['data_obs'])
    
    ndim = 3
    axes = np.array(figure.axes).reshape(ndim,ndim)
    ax = axes[1,1];ax.set_xlim(min_ac, max_ac)
    ax = axes[2,1];ax.set_xlim(min_ac, max_ac);ax.set_ylim(min_ab, max_ab);
    ax.scatter(MW_sim_stats['ca_ratio'], MW_sim_stats['ba_ratio'])
    ax = axes[2,2];ax.set_xlim(min_ab, max_ab)
    ax = axes[0,0];ax.set_xlim(min_w, max_w)
    ax = axes[1,0];ax.set_xlim(min_w, max_w);ax.set_ylim(min_ac, max_ac)
    ax.scatter(MW_sim_stats['width'], MW_sim_stats['ca_ratio'])
    ax = axes[2,0];ax.set_xlim(min_w, max_w);ax.set_ylim(min_ab, max_ab)
    ax.scatter(MW_sim_stats['width'], MW_sim_stats['ba_ratio'])
    children = ax.get_children()
    ax.legend([children[5], children[7], children[4]], [simulation_name[simulation], 'Observations', 'Randomized Obs.'], 
              loc='upper right', bbox_to_anchor=(3.0, 3.0), fontsize=20, markerscale=2)
    

    filename = "../paper/input_{}_obs_MW_n_{}.pdf".format(simulation, n_sat)
    print('saving figure to {}'.format(filename))
    plt.savefig(filename, bbox_inches='tight')
    plt.clf()
    
    plt.close('all')
    
def plot_shape_obs_sims_normed(simulation, n_sat):
    print('simulation {}'.format(simulation))
    simulation_name = {'illustris1':'Illustris1', 'illustris1dark':'Illustris1Dark', 'elvis':'ELVIS'}
    in_path = "../data/{}_mstar_selected_summary/".format(simulation)
    M31_sim_stats, MW_sim_stats = load_experiment(input_path=in_path, n_sat=n_sat, full_data=False)
    
    in_path = "../data/obs_summary/"
    M31_obs_stats, MW_obs_stats = load_experiment(input_path=in_path, n_sat=n_sat, full_data=False)
    M31_obs = get_data_obs(M31_obs_stats, normed=True)
    MW_obs =  get_data_obs(MW_obs_stats, normed=True)

    M31_obs_stats, MW_obs_stats = load_experiment(input_path=in_path, n_sat=n_sat, full_data=True)    
    data_random_obs_M31 = np.array([
        (M31_obs_stats['width_random'] - np.mean(M31_obs_stats['width_random']))/np.std(M31_obs_stats['width_random']),
        (M31_obs_stats['ca_ratio_random'] - np.mean(M31_obs_stats['ca_ratio_random']))/np.std(M31_obs_stats['ca_ratio_random']),
        (M31_obs_stats['ba_ratio_random'] - np.mean(M31_obs_stats['ba_ratio_random']))/np.std(M31_obs_stats['ba_ratio_random'])]).T
                                
    data_random_obs_MW = np.array([
        (MW_obs_stats['width_random'] - np.mean(MW_obs_stats['width_random']))/np.std(MW_obs_stats['width_random']),
        (MW_obs_stats['ca_ratio_random'] - np.mean(MW_obs_stats['ca_ratio_random']))/np.std(MW_obs_stats['ca_ratio_random']),
        (MW_obs_stats['ba_ratio_random'] - np.mean(MW_obs_stats['ba_ratio_random']))/np.std(MW_obs_stats['ba_ratio_random'])]).T

    s = np.array([1.0,2.0,3.0])
    levels = 1-np.exp(-(s**2)/2.0)
    print(np.shape(data_random_obs_MW))
    print(MW_obs)
        
    plt.figure(figsize=(8,5))
    plt.rc('text', usetex=True,)
    plt.rc('font', family='serif', size=25)
    figure = corner.corner(data_random_obs_M31, 
                      quantiles=[0.16, 0.5, 0.84],levels=levels,
                      labels=[r"$w$ M31", r"$c/a$ M31", r"$b/a$ M31"],
                      show_titles=True, title_kwargs={"fontsize": 12}, 
                      truths=M31_obs['data_obs'])
        
        
    min_w = -4; max_w = 4; min_ac = -4; max_ac = 4 ; min_ab = -4; max_ab = 4
    ndim = 3
    axes = np.array(figure.axes).reshape(ndim,ndim)
    ax = axes[1,1];ax.set_xlim(min_ac, max_ac)
    ax = axes[2,1];ax.set_xlim(min_ac, max_ac);ax.set_ylim(min_ab, max_ab);
    ax.scatter(M31_sim_stats['ca_ratio_normed'], M31_sim_stats['ba_ratio_normed'])
    ax = axes[2,2];ax.set_xlim(min_ab, max_ab)
    ax = axes[0,0];ax.set_xlim(min_w, max_w)
    ax = axes[1,0];ax.set_xlim(min_w, max_w);ax.set_ylim(min_ac, max_ac)
    ax.scatter(M31_sim_stats['width_normed'], M31_sim_stats['ca_ratio_normed'])
    ax = axes[2,0];ax.set_xlim(min_w, max_w);ax.set_ylim(min_ab, max_ab)
    ax.scatter(M31_sim_stats['width_normed'], M31_sim_stats['ba_ratio_normed'])
    children = ax.get_children()
    ax.legend([children[5], children[7], children[4]], [simulation_name[simulation], 'Observations', 'Randomized Obs.'], 
              loc='upper right', bbox_to_anchor=(3.0, 3.0), fontsize=20, markerscale=2)
    
    filename = "../paper/input_{}_obs_M31_n_{}_normed.pdf".format(simulation, n_sat)
    print('saving figure to {}'.format(filename))
    plt.savefig(filename, bbox_inches='tight')
    plt.clf()
        
    plt.figure(figsize=(8,5))
    plt.rc('text', usetex=True,)
    plt.rc('font', family='serif', size=25)
    figure = corner.corner(data_random_obs_MW, 
                      quantiles=[0.16, 0.5, 0.84],levels=levels,
                      labels=[r"$w$ MW", r"$c/a$ MW", r"$b/a$ MW"],
                      show_titles=True, title_kwargs={"fontsize": 12}, 
                      truths=MW_obs['data_obs'])
    
    ndim = 3
    axes = np.array(figure.axes).reshape(ndim,ndim)
    ax = axes[1,1];ax.set_xlim(min_ac, max_ac)
    ax = axes[2,1];ax.set_xlim(min_ac, max_ac);ax.set_ylim(min_ab, max_ab);
    ax.scatter(MW_sim_stats['ca_ratio_normed'], MW_sim_stats['ba_ratio_normed'])
    ax = axes[2,2];ax.set_xlim(min_ab, max_ab)
    ax = axes[0,0];ax.set_xlim(min_w, max_w)
    ax = axes[1,0];ax.set_xlim(min_w, max_w);ax.set_ylim(min_ac, max_ac)
    ax.scatter(MW_sim_stats['width_normed'], MW_sim_stats['ca_ratio_normed'])
    ax = axes[2,0];ax.set_xlim(min_w, max_w);ax.set_ylim(min_ab, max_ab)
    ax.scatter(MW_sim_stats['width_normed'], MW_sim_stats['ba_ratio_normed'])
    children = ax.get_children()
    ax.legend([children[5], children[7], children[4]], [simulation_name[simulation], 'Observations', 'Randomized Obs.'], 
              loc='upper right', bbox_to_anchor=(3.0, 3.0), fontsize=20, markerscale=2)
    

    filename = "../paper/input_{}_obs_MW_n_{}_normed.pdf".format(simulation, n_sat)
    print('saving figure to {}'.format(filename))
    plt.savefig(filename, bbox_inches='tight')
    plt.clf()
    
    plt.close('all')

    
def print_covariance(simulation, n_sat):
    def print_ab(a, b, c, d, e, f):
        print("{:.2f} \\pm {:.2f} & {:.2f} \\pm {:.2f} & {:.2f} \\pm {:.2f}\\\\".format(a,b,c,d,e,f))
    simulation_name = {'illustris1':'Illustris-1', 'illustris1dark':'Illustris-1-Dark', 'elvis':'ELVIS'}
    print()
    in_path = "../data/{}_mstar_selected_summary/".format(simulation)
    M31_sim_stats, MW_sim_stats = load_experiment(input_path=in_path, n_sat=n_sat)

    cov_sim_M31 = jacknife_covariance(M31_sim_stats)
    cov_sim_MW = jacknife_covariance(MW_sim_stats)
    
    print('\\subsection{'+'{}'.format(simulation_name[simulation])+', M31, ' + '$N_s={}$'.format(n_sat) + '}')
    print('\\[')
    print('\\Sigma=')
    print('\\begin{bmatrix}')
    for i in range(3):
            print_ab(cov_sim_M31['covariance'][i][0], cov_sim_M31['covariance_error'][i][0], 
                     cov_sim_M31['covariance'][i][1], cov_sim_M31['covariance_error'][i][1],
                     cov_sim_M31['covariance'][i][2], cov_sim_M31['covariance_error'][i][2])
    print('\\end{bmatrix}')
    print('\\]')

    print('\\[')
    print('\\mu=')
    print('\\begin{bmatrix}')
    print_ab(cov_sim_M31['mean'][0], cov_sim_M31['mean_error'][0], 
            cov_sim_M31['mean'][1], cov_sim_M31['mean_error'][1],
            cov_sim_M31['mean'][2], cov_sim_M31['mean_error'][2])
    print('\\end{bmatrix}')
    print('\\]')
    
    print('\\subsection{'+'{}'.format(simulation_name[simulation])+', MW, ' + '$N_s={}$'.format(n_sat) + '}')
    print('\\[')
    print('\\Sigma=')
    print('\\begin{bmatrix}')
    for i in range(3):
            print_ab(cov_sim_MW['covariance'][i][0], cov_sim_MW['covariance_error'][i][0], 
                     cov_sim_MW['covariance'][i][1], cov_sim_MW['covariance_error'][i][1],
                     cov_sim_MW['covariance'][i][2], cov_sim_MW['covariance_error'][i][2])
    print('\\end{bmatrix}')
    print('\\]')

    print('\\[')
    print('\\mu=')
    print('\\begin{bmatrix}')
    print_ab(cov_sim_MW['mean'][0], cov_sim_MW['mean_error'][0], 
            cov_sim_MW['mean'][1], cov_sim_MW['mean_error'][1],
            cov_sim_MW['mean'][2], cov_sim_MW['mean_error'][2])
    print('\\end{bmatrix}')
    print('\\]')
