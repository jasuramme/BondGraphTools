import pytest
import sympy
import BondGraphTools as bgt
import BondGraphTools.sim_tools as sim


@pytest.mark.use_fixture("rlc")
def test_build(rlc):
    assert len(rlc.state_vars) == 2
    assert len(rlc.ports) == 0


@pytest.mark.use_fixture("rlc")
def test_build_and_drive(rlc):
    se = bgt.new("Se")
    assert len(se.control_vars) == 1
    rlc += se

    for comp in rlc.components.values():
        if comp.type == "0":
            rlc.connect(se, comp)
            break

    assert len(rlc.bonds) == 4
    assert len(rlc.control_vars) == 1


def test_symbolic_params():
    r = bgt.new("R", value=sympy.symbols('r'))
    l = bgt.new("I", value=sympy.symbols('l'))
    c = bgt.new("C", value=sympy.symbols('c'))
    kvl = bgt.new("0", name="kvl")

    rlc = r + l + c + kvl

    rlc.connect(r, kvl)
    rlc.connect(l, kvl)
    rlc.connect(c, kvl)

    assert len(rlc.params) == 3

    assert set(rlc.params.values()) & set(sympy.symbols('r, l, c'))


@pytest.mark.use_fixture("rlc")
def test_rlc_con_rel(rlc):

    rel = rlc.constitutive_relations

    eq1 = sympy.sympify("dx_0 - x_1")
    eq2 = sympy.sympify("dx_1 + x_0 + x_1")

    for r in rel:
        assert r in (eq1, eq2)

    assert "x_0" in rlc.state_vars
    assert "x_1" in rlc.state_vars


@pytest.mark.usefixture("rlc")
def test_add_forcing(rlc):
    port = rlc.make_port()

    assert port == 0

    rlc.connect((rlc, port), "0_0")

    assert rlc.ports == {
        0: (rlc, port)
    }

    ts, ps, cv = rlc.basis_vectors

    assert len(ps) == 1

    assert rlc.constitutive_relations == list(
        sympy.sympify("dx_0 - x_1, dx_1 + f_0 + x_0 + x_1, e_0 - x_1")
    )


def test_tf():
    l = bgt.new("I", value=1)
    c = bgt.new("C", value=1)
    tf = bgt.new("TF", value=0.5)

    tflc = tf + l + c
    tflc.connect(l, (tf, 1))
    tflc.connect(c, (tf, 0))

    c,m,lp,nlp = tflc._system_rep()
    assert not nlp


def test_se():

    Se = bgt.new('Se', value=1)
    c = bgt.new('C', value=1)
    vc = Se + c
    assert Se.constitutive_relations == [sympy.sympify("e_0 - 1")]
    vc.connect(Se, c)
    assert vc.constitutive_relations == [sympy.sympify("dx_0"), sympy.sympify("x_0 - 1")]