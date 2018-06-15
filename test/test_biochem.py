import pytest

import sympy

import BondGraphTools as bgt
from BondGraphTools.exceptions import InvalidPortException
from BondGraphTools.algebra import extract_coefficients, inverse_coord_maps
from BondGraphTools.reaction_builder import Reaction_Network

def test_make_a_to_b():

    A = bgt.new("Ce", library="BioChem", value=[1, 1, 1])
    B = bgt.new("Ce", library="BioChem", value=[1, 1, 1])

    Re = bgt.new("Re", library="BioChem", value={"R": 1, "T": 1})

    a_to_b = A + Re + B
    with pytest.raises(InvalidPortException):
        a_to_b.connect(A, Re)

    assert 0 in Re.ports
    a_to_b.connect(A, (Re, 0))
    a_to_b.connect(B, (Re, 1))

    assert Re.control_vars == ['r']
    assert list(a_to_b.state_vars.keys()) == ['x_0', 'x_1']
    assert list(a_to_b.control_vars.keys()) == ['u_0']
    assert not a_to_b.ports


def test_re_con_rel():
    Re = bgt.new("Re", library="BioChem", value={"R": 1, "T": 1})

    r = Re.constitutive_relations[1]

    coords = list(sympy.sympify("e_0,f_0,e_1,f_1,r"))
    local_map = {c:i for i,c in enumerate(coords)}

    coeff_dict, nlin = extract_coefficients(r, local_map, coords)

    assert coeff_dict == {1: 1}
    assert nlin

    mappings, coords = inverse_coord_maps(*Re.basis_vectors)
    assert mappings
    assert coords

    for r in Re.get_relations_iterator(mappings, coords):
        assert r in [
            ({1:1, 3:1}, 0), ({1:1}, sympy.sympify("-r*exp(e_0) + r*exp(e_1)"))
        ]

#
# def test_a_to_b_system():
#     A = bgt.new("Ce", library="BioChem", value=[0, 1, 1, 1])
#     B = bgt.new("Ce", library="BioChem", value=[0, 1, 1, 1])
#
#     Re = bgt.new("Re", library="BioChem", value={'k':1, "R": 1, "T": 1})
#     tf_in = bgt.new("Tf", value=-1)
#     tf_out = bgt.new("Tf", value=-1)
#     a_to_b = A + Re + B + tf_in + tf_out
#
#     a_to_b.connect(A, (tf_in,0))
#     a_to_b.connect(B, (tf_out, 1))
#     a_to_b.connect((Re, 0), (tf_in,1))
#     a_to_b.connect((Re, 1), (tf_out, 0))
#
#     coords, mappings, linear_op, nonlinear_op = a_to_b._system_rep()
#     print(coords)
#     print(mappings)
#     print([linear_op, nonlinear_op])
#     assert False


def test_stiochiometry():
    A = bgt.new("Ce", library="BioChem", value=[1, 1, 1])
    B = bgt.new("Ce", library="BioChem", value=[1, 1, 1])

    Re = bgt.new("Re", library="BioChem", value={'r': 1, "R": 1, "T": 1})
    Yin = bgt.new('Y', library="BioChem")
    bg = A + B + Re + Yin

    assert 0 in Yin._fixed_ports
    assert Yin.ports[0]["name"] == "Complex"
    assert len(Yin.ports) == 1

    bg.connect((Re, 0), (Yin, 0))
    assert len(Yin.ports) == 1

    bg.connect(A, (Yin, 1))
    assert Yin.ports[1] == 1

    bg.connect(B, (Yin, 2))
    assert Yin.ports[2] == 1

    assert Yin.ports == {0:{"name":"Complex","value":-1}, 1:1, 2:1}


def test_a_to_b_model():
    A = bgt.new("Ce", library="BioChem", value=[1, 1, 1])
    B = bgt.new("Ce", library="BioChem", value=[1, 1, 1])

    Re = bgt.new("Re", library="BioChem", value={'r': 1, "R": 1, "T": 1})

    Y_A = bgt.new('Y', library="BioChem")
    Y_B = bgt.new('Y', library="BioChem")

    a_to_b = A + Re + B + Y_A + Y_B

    a_to_b.connect(A, (Y_A, 1))
    a_to_b.connect(B, (Y_B, 1))
    a_to_b.connect((Re, 0), (Y_A, 0))
    a_to_b.connect((Re, 1), (Y_B, 0))
    eqns ={
        sympy.sympify("dx_0 + x_0 -x_1"), sympy.sympify("dx_1 + x_1 -x_0")
    }
    for relation in a_to_b.constitutive_relations:
        assert relation in eqns


def test_ab_to_c_model():

    A = bgt.new("Ce", library="BioChem", value=[1, 1, 1])
    B = bgt.new("Ce", library="BioChem", value=[1, 1, 1])
    C = bgt.new("Ce", library="BioChem", value=[1, 1, 1])
    Re = bgt.new("Re", library="BioChem", value={'r': 1, "R": 1, "T": 1})
    Y_AB = bgt.new('Y', library="BioChem")
    Y_C = bgt.new('Y', library="BioChem")

    assert Y_AB.ports[0]
    assert Y_AB._fixed_ports == {0}
    bg = A + B + Re + Y_AB + C + Y_C
    bg.connect(A, (Y_AB, 1))

    assert Y_AB.ports[1] == 1
    bg.connect(B, (Y_AB, 2))
    bg.connect((Re, 0), (Y_AB, 0))
    bg.connect((Re, 1), (Y_C, 0))
    bg.connect((Y_C, 1), C)

    assert 0 in Y_AB._fixed_ports
    assert 0 in Y_AB.ports

    eqns = {
        sympy.sympify("dx_0 + x_0*x_1 - x_2"),
        sympy.sympify("dx_1 + x_0*x_1 - x_2"),
        sympy.sympify("dx_2 - x_0*x_1 + x_2")
    }

    for relation in bg.constitutive_relations:
        assert relation in eqns


def test_new_reaction_network():

    rn = Reaction_Network(name="A+B to C")
    rn.add_reaction(
        "A+B=C"
    )
    assert rn.species ==["A","B","C"]
    assert rn.forward_stoichiometry == sympy.Matrix([[0],[0],[1]])
    assert rn.reverse_stoichiometry == sympy.Matrix([[1], [1], [0]])
    assert rn.stoichiometry == sympy.Matrix([[-1],[-1],[1]])


def test_rn_to_bond_graph():
    rn = Reaction_Network(name="A+B to C", reactions="A+B=C")

    system = rn.as_network_model(normalised=True)
    for comp in system.components.values():
        if comp.type == 'Y':
            for port in comp.ports:
                if port != 0:
                    assert comp.ports[port] == 1

    assert len(system.state_vars) == 3
    assert len(system.control_vars) == 4


def test_cat_rn():
    reactions = [
        "E + S = ES", "ES = E+P"
    ]
    rn = Reaction_Network(reactions=reactions, name="Catalysed Reaction")
    assert rn._species["ES"] == 2
    assert len(rn._reactions) == 2

