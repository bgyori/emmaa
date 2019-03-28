import json
import pickle
import datetime
from emmaa.model import EmmaaModel
from emmaa.statements import EmmaaStatement
from emmaa.priors.cancer_prior import TcgaCancerPrior
from emmaa.priors.prior_stmts import get_stmts_for_gene_list
from emmaa.priors.reactome_prior import find_drugs_for_genes
from emmaa.priors.reactome_prior import make_prior_from_genes

'''
def get_terms(ctype):
    tcp = TcgaCancerPrior(ctype, 'stmts_by_pair_type.csv',
                          mutation_cache=f'mutations_{ctype}.json')
    nodes = tcp.make_prior(pct_heat_threshold=99)
    cancer_terms = tcp.search_terms_from_nodes(nodes)
    drug_terms = tcp.find_drugs_for_genes(nodes)
    return cancer_terms, drug_terms
'''


def get_top_genes(ctype, k):
    mut_file = f'../models/{ctype}/prior/mutations.json'
    with open(mut_file, 'r') as fh:
        mut_counts = json.load(fh)
    norm_mut_counts = {g: TcgaCancerPrior.normalize_mutation_count(g, n) for
                       g, n in mut_counts.items()}
    sorted_counts = sorted(norm_mut_counts.items(), key=lambda x: x[1],
                           reverse=True)
    top_genes = [s[0] for s in sorted_counts[:k]]
    return top_genes


def load_config(ctype):
    fname = f'../models/{ctype}/config.json'
    with open(fname, 'r') as fh:
        config = json.load(fh)
    # TODO: make the search term entries here SearchTerm objects
    return config


def save_config(ctype, terms):
    fname = f'../models/{ctype}/config.json'
    config = load_config(ctype)
    config['search_terms'] = [term.to_json() for term in terms]
    with open(fname, 'w') as fh:
        json.dump(config, fh, indent=1)


def save_prior(ctype, stmts):
    with open(f'../models/{ctype}/reactome_prior.pkl', 'wb') as fh:
        pickle.dump(stmts, fh)


def upload_prior(ctype, config):
    fname = f'../models/{ctype}/prior_stmts.pkl'
    with open(fname, 'rb') as fh:
        stmts = pickle.load(fh)
    estmts = [EmmaaStatement(stmt, datetime.datetime.now(), [])
              for stmt in stmts]
    model = EmmaaModel(ctype, config)
    model.add_statements(estmts)
    model.upload_to_ndex()


if __name__ == '__main__':
    cancer_types = ('aml', 'brca', 'luad', 'paad', 'prad', 'skcm',)
    for ctype in cancer_types:
        top_genes = get_top_genes(ctype, 5)
        cancer_terms = make_prior_from_genes(top_genes)
        drug_terms = find_drugs_for_genes(cancer_terms)
        gene_names = [g.name for g in cancer_terms]
        drug_names = [d.name for d in drug_terms]
        terms = cancer_terms + drug_terms
        save_config(ctype, terms)
        prior_stmts = get_stmts_for_gene_list(gene_names, drug_names)
        save_prior(ctype, prior_stmts)
