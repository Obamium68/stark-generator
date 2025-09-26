"""
STARK Proof Verifier
"""
from app.core.merkle import verify_decommitment
from app.core.field import FieldElement


def get_cp_value(domain, idx, compos_factors, fx, fgx, fggx, target):
    """Calcola il valore del polinomio di composizione."""
    domain_element = domain[idx]
    g = FieldElement.generator() ** ((3 * 2**30) // 1024)
    
    # Calcolo dei tre componenti del polinomio di composizione
    f1 = compos_factors[0] * (fx - 1) / (domain_element - 1)
    f2 = compos_factors[1] * (fx - target) / (domain_element - g**1022)
    
    vanishing_poly = (domain_element**1024 - 1) / (
        (domain_element - g**1021) *
        (domain_element - g**1022) *
        (domain_element - g**1023)
    )
    f3 = compos_factors[2] * (fggx - fgx**2 - fx**2) / vanishing_poly
    
    return f1 + f2 + f3


def verify_proof(proof):
    """Verifica la validità di una proof utilizzando il protocollo FRI."""
    verification_errors = []
    
    try:
        # Estrazione dei parametri dalla proof
        mod = proof["mod"]
        target = FieldElement(int(proof["target"]))
        interp_poly_root = proof["interp_poly_root"]
        compos_factors = [
            proof["compos_factors"]["alpha_0"],
            proof["compos_factors"]["alpha_1"],
            proof["compos_factors"]["alpha_2"]
        ]
        folding_poly_coeffs = proof["fri_commitment"]["folding_poly_coeffs"]
        n_layers = len(folding_poly_coeffs)
        layer_roots = proof["fri_commitment"]["layer_roots"]
        final_constant = proof["fri_commitment"]["final_constant"]
        query_num = proof["fri_decommitments"]["query_num"]
        queries = proof["fri_decommitments"]["queries"]
        dom_size = proof["dom_size"]
        
    except KeyError as e:
        verification_errors.append(f"Missing required field in proof: {e}")
        return False, verification_errors
    except Exception as e:
        verification_errors.append(f"Error parsing proof data: {e}")
        return False, verification_errors
    
    # Calcolo delle dimensioni dei domini per ogni layer
    layer_domain_sizes = [dom_size // (2**i) for i in range(n_layers)]
    
    # Costruzione del dominio di valutazione iniziale
    w = FieldElement.generator()
    h = w ** ((3 * 2**30) // dom_size)
    H = [h**i for i in range(dom_size)]
    domain = [w * x for x in H]
    
    # Costruzione dei domini per ogni layer FRI
    layer_domains = []
    current_domain = domain
    
    for i in range(n_layers):
        layer_domains.append(current_domain)
        current_domain = [d**2 for d in current_domain[:len(current_domain)//2]]
    
    # Verifica di ogni query
    for i in range(query_num):
        query = queries[i]
        idx = query["idx"]
        f_x = query["f_x"]
        f_gx = query["f_gx"]
        f_ggx = query["f_ggx"]
        layers= query["fri_layers"]
       
        f_x_val = FieldElement(int(query["f_x"]["val"]))
        f_gx_val = FieldElement(int(query["f_gx"]["val"]))
        f_ggx_val = FieldElement(int(query["f_ggx"]["val"]))
        
        # Verifica dei decommitment per i valori del polinomio
        decommitment_f_x_valid = verify_decommitment(idx, f_x_val, f_x["auth_path"], interp_poly_root)
        if not decommitment_f_x_valid:
            verification_errors.append(f"Query {i}: Decommitment verification failed for f(x) at index {idx}")
            
        decommitment_f_gx_valid = verify_decommitment(idx + 8, f_gx_val, f_gx["auth_path"], interp_poly_root)
        if not decommitment_f_gx_valid:
            verification_errors.append(f"Query {i}: Decommitment verification failed for f(gx) at index {idx + 8}")
            
        decommitment_f_ggx_valid = verify_decommitment(idx + 16, f_ggx_val, f_ggx["auth_path"], interp_poly_root)
        if not decommitment_f_ggx_valid:
            verification_errors.append(f"Query {i}: Decommitment verification failed for f(ggx) at index {idx + 16}")
        
        # Verifica che l'ultimo valore corrisponda alla costante finale
        final_constant_valid = (query["last_val"] == final_constant)
        if not final_constant_valid:
            verification_errors.append(f"Query {i}: Final constant verification failed. Expected: {final_constant}, Got: {query['last_val']}")
        
        # Verifica di ogni layer FRI
        for j in range(n_layers):
            cur_layer = layers[f"layer_{j}"]
            
            # Per il primo layer, il valore deve corrispondere al composition polynomial
            if j == 0:
                expected_cp_value = get_cp_value(
                    domain, idx, compos_factors, f_x_val, f_gx_val, f_ggx_val, target
                )
                composition_poly_valid = (expected_cp_value == int(cur_layer["val"]))
                if not composition_poly_valid:
                    verification_errors.append(f"Query {i}, Layer {j}: Composition polynomial verification failed. Expected: {expected_cp_value}, Got: {int(cur_layer['val'])}")

            # Verifica dei decommitment per il layer corrente
            cur_layer_val, sib_layer_val = FieldElement(int(cur_layer["val"])), FieldElement(int(cur_layer["sib_val"]))
            layer_idx, sib_idx = cur_layer["idx"], cur_layer["idx"] + layer_domain_sizes[j] // 2
            
            layer_decommitment_valid = verify_decommitment(
                layer_idx, cur_layer_val, cur_layer["auth_path"], layer_roots[j]
            )
            if not layer_decommitment_valid:
                verification_errors.append(f"Query {i}, Layer {j}: Layer decommitment verification failed at index {layer_idx}")
                
            sib_decommitment_valid = verify_decommitment(
                sib_idx, sib_layer_val, cur_layer["sib_auth_path"], layer_roots[j]
            )
            if not sib_decommitment_valid:
                verification_errors.append(f"Query {i}, Layer {j}: Sibling decommitment verification failed at index {sib_idx}")
            
            # Verifica del FRI folding
            try:
                beta = FieldElement(folding_poly_coeffs[j])
                    
                domain_element = layer_domains[j][layer_idx]
                    
                p_d = cur_layer_val
                p_neg_d = sib_layer_val
                    
                folded_value = (p_d + p_neg_d) / FieldElement(2) + beta * (p_d - p_neg_d) / (FieldElement(2) * domain_element)
                
                if j + 1 < n_layers:
                    next_layer = layers[f"layer_{j+1}"]
                    next_layer_val = FieldElement(int(next_layer["val"]))
                    folding_verification_valid = (folded_value == next_layer_val)
                    if not folding_verification_valid:
                        verification_errors.append(f"Query {i}, Layer {j}: FRI folding verification failed. Expected: {next_layer_val}, Got: {folded_value}")
                elif j == n_layers - 1:
                    final_folding_valid = (int(final_constant) == folded_value)
                    if not final_folding_valid:
                        verification_errors.append(f"Query {i}, Layer {j}: Final folding verification failed. Expected: {final_constant}, Got: {folded_value}")
                        
            except Exception as e:
                verification_errors.append(f"Query {i}, Layer {j}: Error in FRI folding calculation: {e}")
    
    is_valid = len(verification_errors) == 0
    return is_valid, verification_errors