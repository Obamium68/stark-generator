from eth_hash.auto import keccak
from polynomial import X, interpolate_poly, Polynomial
from merkle import MerkleTree
from field import FieldElement
from FRI_functions import decommit_fri, commit_fri
import json, time

def keccak256(data: bytes) -> str:
    return keccak(data).hex()

def nhash(data):
    hex_dig = keccak256(data.encode())
    return int(hex_dig, 16)

def get_secret(data, integer_cap):
    return (nhash(str({data})) % integer_cap)

def get_fibonacci_sequence(data):
    my_secret = get_secret(data, FieldElement.k_modulus)
    t = [FieldElement(1), FieldElement(my_secret)]
    while len(t) < 1023:
        t.append(t[-2] ** 2 + t[-1] ** 2)
    return t    

def generate_proof(data, query_num, ver):
    verifier_data = json.loads(ver)
    proof = {}
    p_dom_size = 1024
    eval_dom_size = 8192
    target_idx = 1022

    proof["timestamp"] = time.time()
    proof["mod"] = FieldElement.k_modulus
    proof["dom_size"] = eval_dom_size
    proof["interp_domain_size"] = p_dom_size

    fib = get_fibonacci_sequence(data)
    target = fib[target_idx]
    proof["target"] = str(target)

    g = FieldElement.generator() ** ((3 * 2**30)//p_dom_size)
    G = [g ** i for i in range(p_dom_size)]
    proof["domain_gen"] = str(g)

    w = FieldElement.generator()
    proof["mul_field_gen"] = str(w)
    h = w ** ((3*2 ** 30 ) // eval_dom_size)
    H = [h ** i for i in range(eval_dom_size)]
    domain = [w * x for x in H]

    p = interpolate_poly(G[:-1], fib)
    ev_points = [p.eval(d) for d in domain]
    f_merkle = MerkleTree(ev_points)
    proof["interp_poly_root"] = f_merkle.root

    numer0 = p - 1
    denom0 = X - 1
    p0 = numer0 / denom0

    numer1 = p - target
    denom1 = X - g**1022
    p1 = numer1 / denom1

    numer2 = p(g**2 * X) - p(g * X)**2 - p**2
    denom2 = (X**1024 - 1) / ((X - g**1021) * (X - g**1022) * (X - g**1023))
    p2 = numer2 / denom2

    poly_factors = verifier_data["poly_coeffs"]
    factor0, factor1, factor2 = poly_factors[0], poly_factors[1], poly_factors[2]
    proof["compos_factors"] = {
        "alpha_0": factor0,
        "alpha_1": factor1,
        "alpha_2": factor2
    }

    cp: Polynomial = factor0*p0 + factor1*p1 + factor2*p2
    cp_eval = [cp.eval(d) for d in domain]
    cp_merkle = MerkleTree(cp_eval)
    proof["compos_poly_root"] = cp_merkle.root

    fri_polys, fri_domains, fri_layers, fri_merkles, fri_on_proof = commit_fri(cp, domain, cp_eval, cp_merkle, verifier_data["folding_coeffs"])
    proof["fri_commitment"] = fri_on_proof
    challenges = verifier_data["challenges"]
    proof["fri_decommitments"] = decommit_fri(ev_points, f_merkle, fri_layers, fri_merkles, challenges, query_num)
    return proof

