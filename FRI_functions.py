from merkle import MerkleTree
from polynomial import Polynomial


def next_fri_domain(fri_domain):
    return [x ** 2 for x in fri_domain[:len(fri_domain) // 2]]


def commit_fri(cp, domain, cp_eval, cp_merkle,coeffs):    
    fri_on_proof={}
    fri_polys = [cp]
    fri_domains = [domain]
    fri_layers = [cp_eval]
    fri_merkles = [cp_merkle]
    i=0
    layer_roots=[cp_merkle.root]

    while fri_polys[-1].degree() > 0:
        beta = coeffs[i]
        next_poly, next_domain, next_layer = next_fri_layer(fri_polys[-1], fri_domains[-1], beta)
    
        fri_polys.append(next_poly)
        fri_domains.append(next_domain)
        fri_layers.append(next_layer)
        fri_merkles.append(MerkleTree(next_layer))
        layer_roots.append(fri_merkles[-1].root)
        i += 1
    fri_on_proof["layer_roots"]=layer_roots
    fri_on_proof["folding_poly_coeffs"]=coeffs[:i]
    
    fri_on_proof["final_constant"] = str(fri_polys[-1].poly[0])
    return fri_polys, fri_domains, fri_layers, fri_merkles, fri_on_proof



def next_fri_polynomial(poly,  beta):
    odd_coefficients = poly.poly[1::2]
    even_coefficients = poly.poly[::2]
    odd = beta * Polynomial(odd_coefficients)
    even = Polynomial(even_coefficients)
    return odd + even


def next_fri_layer(poly, domain, beta):
    next_poly = next_fri_polynomial(poly, beta)
    next_domain = next_fri_domain(domain)
    next_layer = [next_poly(x) for x in next_domain]
    return next_poly, next_domain, next_layer



def decommit_on_fri_layers(idx, fri_layers, fri_merkles):
    layers = {}

    for layer_num, (layer, merkle) in enumerate(zip(fri_layers[:-1], fri_merkles[:-1])):
        fri_l = {}
        length = len(layer)
        idx = idx % length
        sib_idx = (idx + length // 2) % length

        fri_l["idx"] = idx
        fri_l["val"] = str(layer[idx])
        fri_l["auth_path"] = merkle.get_authentication_path(idx)
        fri_l["sib_val"] = str(layer[sib_idx])
        fri_l["sib_auth_path"] = merkle.get_authentication_path(sib_idx)


        layers[f"layer_{layer_num}"] = fri_l
    
    return layers,str(fri_layers[-1][0])

def decommit_on_query(idx, f_eval, f_merkle:MerkleTree, fri_layers, fri_merkles):
    assert idx + 16 < len(f_eval), f'query index: {idx} is out of range. Length of layer: {len(f_eval)}.'

    query = {"idx": idx}

    query["f_x"] = {
        "val": str(f_eval[idx]),
        "auth_path": f_merkle.get_authentication_path(idx)
    }

    query["f_gx"] = {
        "val": str(f_eval[idx + 8]),
        "auth_path": f_merkle.get_authentication_path(idx + 8)
    }

    query["f_ggx"] = {
        "val": str(f_eval[idx + 16]),
        "auth_path": f_merkle.get_authentication_path(idx + 16)
    }

    query["fri_layers"], query["last_val"]= decommit_on_fri_layers(idx, fri_layers, fri_merkles)
    return query

def decommit_fri(f_eval, f_merkle, fri_layers, fri_merkles, challenges, query_num=3):
    queries = []

    for i in range(query_num):
        r = challenges[i]
        queries.append(decommit_on_query(r, f_eval, f_merkle, fri_layers, fri_merkles))

    return {
        "query_num": query_num,
        "queries": queries,
        "fri_last_val": str(fri_layers[-1][0])
    }