"""
Domain-Specific Keywords Database


This module contains comprehensive keyword collections for various academic domains
including mathematics, physics, chemistry, and engineering.


"""

# ============================================================
# MATHEMATICS KEYWORDS / 
# ============================================================

ALGEBRA_KEYWORDS = {
    # Basic algebra / 
    "equation", "variable", "constant", "coefficient", "polynomial",
    "monomial", "binomial", "trinomial", "quadratic", "linear",
    "exponential", "logarithm", "logarithmic", "exponent", "power",
    "root", "square root", "cube root", "radical", "factor",
    "factorization", "expansion", "simplification", "expression",
    "term", "like terms", "inequality", "absolute value",

    # Advanced algebra / 
    "matrix", "matrices", "determinant", "eigenvalue", "eigenvector",
    "system of equations", "simultaneous", "substitution", "elimination",
    "cramer's rule", "gaussian elimination", "row reduction",

    # Functions / 
    "function", "domain", "range", "inverse", "composition",
    "bijection", "injection", "surjection", "mapping", "transformation"
}

GEOMETRY_KEYWORDS = {
    # 2D shapes / 
    "triangle", "square", "rectangle", "circle", "ellipse",
    "polygon", "pentagon", "hexagon", "octagon", "parallelogram",
    "trapezoid", "rhombus", "kite", "quadrilateral",

    # 3D shapes / 
    "sphere", "cube", "cylinder", "cone", "pyramid", "prism",
    "tetrahedron", "polyhedron", "torus", "hemisphere",

    # Measurements / 
    "area", "perimeter", "circumference", "diameter", "radius",
    "volume", "surface area", "lateral area", "height", "width",
    "length", "depth", "diagonal", "side", "edge", "face", "vertex",

    # Angles / 
    "angle", "acute", "obtuse", "right angle", "straight angle",
    "reflex", "complementary", "supplementary", "vertical angles",
    "adjacent", "corresponding", "alternate", "interior", "exterior",

    # Geometric properties / 
    "congruent", "similar", "parallel", "perpendicular", "tangent",
    "secant", "chord", "arc", "sector", "segment", "midpoint",
    "bisector", "median", "altitude", "centroid", "orthocenter",
    "incenter", "circumcenter", "inscribed", "circumscribed"
}

TRIGONOMETRY_KEYWORDS = {
    # Trig functions / 
    "sine", "cosine", "tangent", "cotangent", "secant", "cosecant",
    "sin", "cos", "tan", "cot", "sec", "csc",
    "arcsin", "arccos", "arctan", "inverse trig",

    # Identities / 
    "pythagorean", "identity", "double angle", "half angle",
    "sum formula", "difference formula", "product formula",

    # Triangle properties / 
    "law of sines", "law of cosines", "law of tangents",
    "hypotenuse", "opposite", "adjacent", "right triangle",

    # Angular measurements / 
    "radian", "degree", "revolution", "period", "amplitude",
    "phase shift", "frequency"
}

CALCULUS_KEYWORDS = {
    # Derivatives / 
    "derivative", "differentiation", "differential", "gradient",
    "slope", "tangent line", "rate of change", "velocity",
    "acceleration", "higher order", "partial derivative",
    "chain rule", "product rule", "quotient rule", "power rule",

    # Integrals / 
    "integral", "integration", "antiderivative", "definite integral",
    "indefinite integral", "riemann sum", "fundamental theorem",
    "substitution", "integration by parts", "u-substitution",
    "area under curve", "volume of revolution", "disk method",
    "shell method", "washer method",

    # Limits / 
    "limit", "continuity", "continuous", "discontinuous",
    "asymptote", "horizontal asymptote", "vertical asymptote",
    "oblique asymptote", "approaching", "tends to",

    # Series / 
    "series", "sequence", "convergence", "divergence",
    "taylor series", "maclaurin series", "power series",
    "geometric series", "harmonic series", "alternating series",

    # Multivariable / 
    "partial", "gradient", "divergence", "curl", "laplacian",
    "vector field", "line integral", "surface integral",
    "green's theorem", "stokes' theorem", "divergence theorem"
}

STATISTICS_KEYWORDS = {
    # Descriptive statistics / 
    "mean", "median", "mode", "average", "variance", "standard deviation",
    "range", "quartile", "percentile", "interquartile range",
    "outlier", "deviation", "distribution", "frequency",
    "histogram", "box plot", "scatter plot",

    # Probability / 
    "probability", "chance", "likelihood", "odds", "random",
    "event", "outcome", "sample space", "independent", "dependent",
    "conditional probability", "bayes theorem", "permutation",
    "combination", "factorial", "binomial", "normal distribution",
    "poisson", "exponential distribution", "uniform distribution",

    # Statistical inference / 
    "hypothesis", "null hypothesis", "alternative hypothesis",
    "p-value", "significance", "confidence interval", "t-test",
    "z-test", "chi-square", "anova", "regression", "correlation",
    "coefficient", "r-squared", "residual", "error", "sample",
    "population", "bias", "sampling"
}

NUMBER_THEORY_KEYWORDS = {
    # Basic concepts / 
    "prime", "composite", "factor", "multiple", "divisor",
    "greatest common divisor", "gcd", "least common multiple", "lcm",
    "coprime", "relatively prime", "modular", "modulo", "congruence",

    # Advanced concepts / 
    "diophantine", "fermat", "euler", "totient", "chinese remainder",
    "quadratic residue", "primitive root", "discrete logarithm"
}

# Combine all math keywords / 
MATH_KEYWORDS = (
    ALGEBRA_KEYWORDS | GEOMETRY_KEYWORDS | TRIGONOMETRY_KEYWORDS |
    CALCULUS_KEYWORDS | STATISTICS_KEYWORDS | NUMBER_THEORY_KEYWORDS
)


# ============================================================
# PHYSICS KEYWORDS / 
# ============================================================

MECHANICS_KEYWORDS = {
    # Kinematics / 
    "motion", "displacement", "distance", "velocity", "speed",
    "acceleration", "deceleration", "uniform motion", "projectile",
    "trajectory", "parabolic", "freefall", "vertical", "horizontal",
    "relative motion", "reference frame", "position", "time",

    # Dynamics / 
    "force", "net force", "resultant", "newton", "mass", "weight",
    "inertia", "momentum", "impulse", "collision", "elastic",
    "inelastic", "coefficient of restitution", "friction",
    "static friction", "kinetic friction", "normal force",
    "tension", "applied force", "gravity", "gravitational force",

    # Newton's laws / 
    "newton's first law", "newton's second law", "newton's third law",
    "action", "reaction", "equilibrium", "balanced forces",

    # Work and energy / 
    "work", "energy", "kinetic energy", "potential energy",
    "gravitational potential", "elastic potential", "spring",
    "hooke's law", "power", "efficiency", "conservation of energy",
    "mechanical energy", "joule", "watt",

    # Rotational motion / 
    "rotation", "angular", "angular velocity", "angular acceleration",
    "torque", "moment", "lever arm", "moment of inertia",
    "rotational kinetic energy", "angular momentum", "centripetal",
    "centrifugal", "circular motion", "period", "frequency", "rpm",
    "radian per second"
}

THERMODYNAMICS_KEYWORDS = {
    # Temperature and heat / 
    "temperature", "heat", "thermal", "celsius", "fahrenheit",
    "kelvin", "absolute zero", "thermal expansion", "coefficient",
    "specific heat", "heat capacity", "calorimetry", "latent heat",
    "fusion", "vaporization", "sublimation", "condensation",

    # Laws of thermodynamics / 
    "first law", "second law", "third law", "zeroth law",
    "internal energy", "enthalpy", "entropy", "free energy",
    "gibbs", "helmholtz",

    # Processes / 
    "isothermal", "adiabatic", "isobaric", "isochoric",
    "reversible", "irreversible", "cycle", "carnot", "efficiency",
    "heat engine", "refrigerator", "heat pump",

    # Gas laws / 
    "ideal gas", "pressure", "volume", "pv=nrt", "boyle's law",
    "charles's law", "gay-lussac's law", "avogadro's law",
    "combined gas law", "partial pressure", "dalton's law",
    "kinetic theory", "mean free path", "rms velocity"
}

ELECTROMAGNETISM_KEYWORDS = {
    # Electrostatics / 
    "charge", "electric charge", "coulomb", "electric field",
    "electric potential", "voltage", "potential difference",
    "capacitance", "capacitor", "dielectric", "permittivity",
    "coulomb's law", "gauss's law", "electric flux",
    "equipotential", "polarization",

    # Current electricity / 
    "current", "electric current", "ampere", "resistance", "resistor",
    "ohm", "ohm's law", "conductivity", "resistivity",
    "series", "parallel", "kirchhoff", "junction rule", "loop rule",
    "emf", "electromotive force", "internal resistance",
    "power dissipation", "joule heating",

    # Circuits / 
    "circuit", "closed circuit", "open circuit", "short circuit",
    "battery", "cell", "terminal", "node", "mesh", "branch",
    "thevenin", "norton", "superposition", "wheatstone bridge",

    # Magnetism / 
    "magnetic", "magnetic field", "magnetic flux", "tesla",
    "gauss", "weber", "permeability", "electromagnet", "solenoid",
    "toroid", "biot-savart", "ampere's law", "lorentz force",
    "magnetic dipole", "magnetic moment",

    # Electromagnetic induction / 
    "induction", "faraday's law", "lenz's law", "induced emf",
    "induced current", "mutual inductance", "self inductance",
    "inductor", "transformer", "eddy current", "motional emf",

    # AC circuits / 
    "alternating current", "ac", "dc", "direct current",
    "frequency", "angular frequency", "phase", "impedance",
    "reactance", "inductive", "capacitive", "resonance",
    "rlc circuit", "power factor", "rms", "peak value",

    # Electromagnetic waves / 
    "electromagnetic wave", "maxwell's equations", "electromagnetic spectrum",
    "radio wave", "microwave", "infrared", "visible light",
    "ultraviolet", "x-ray", "gamma ray", "photon", "wave-particle"
}

OPTICS_KEYWORDS = {
    # Geometric optics / 
    "light", "ray", "reflection", "refraction", "snell's law",
    "index of refraction", "critical angle", "total internal reflection",
    "mirror", "plane mirror", "concave mirror", "convex mirror",
    "spherical mirror", "focal length", "focal point", "center of curvature",
    "magnification", "real image", "virtual image", "object distance",
    "image distance", "mirror equation",

    # Lenses / 
    "lens", "convex lens", "concave lens", "converging", "diverging",
    "thin lens", "thick lens", "lens equation", "optical power",
    "diopter", "aberration", "chromatic aberration",
    "spherical aberration", "astigmatism",

    # Wave optics / 
    "interference", "diffraction", "polarization", "double slit",
    "young's experiment", "thin film", "constructive interference",
    "destructive interference", "path difference", "coherent",
    "wavelength", "amplitude", "intensity", "malus's law",
    "brewster's angle", "bragg's law", "grating", "fringe",

    # Quantum optics / 
    "photoelectric effect", "photon", "planck's constant",
    "work function", "de broglie", "wave-particle duality",
    "compton scattering", "black body radiation"
}

WAVES_KEYWORDS = {
    # Wave properties / 
    "wave", "transverse", "longitudinal", "mechanical wave",
    "electromagnetic wave", "wavelength", "frequency", "period",
    "amplitude", "crest", "trough", "compression", "rarefaction",
    "wave speed", "phase", "phase velocity", "group velocity",

    # Wave phenomena / 
    "superposition", "interference", "diffraction", "reflection",
    "refraction", "dispersion", "doppler effect", "standing wave",
    "node", "antinode", "resonance", "harmonics", "fundamental frequency",
    "overtone", "beat frequency", "wave equation",

    # Sound / 
    "sound", "acoustic", "ultrasound", "infrasound", "loudness",
    "pitch", "timbre", "decibel", "intensity level", "sonic boom",
    "echo", "reverberation", "absorption", "transmission"
}

MODERN_PHYSICS_KEYWORDS = {
    # Quantum mechanics / 
    "quantum", "quanta", "quantization", "wave function",
    "schrodinger equation", "uncertainty principle", "heisenberg",
    "quantum state", "eigenstate", "superposition", "entanglement",
    "quantum tunneling", "quantum harmonic oscillator",
    "hydrogen atom", "orbital", "quantum number", "spin",
    "pauli exclusion", "fermi", "boson", "fermion",

    # Relativity / 
    "relativity", "special relativity", "general relativity",
    "frame of reference", "inertial frame", "time dilation",
    "length contraction", "lorentz transformation", "spacetime",
    "speed of light", "invariant", "proper time", "proper length",
    "relativistic mass", "mass-energy equivalence", "e=mc^2",
    "minkowski space", "worldline",

    # Nuclear physics / 
    "nucleus", "proton", "neutron", "nucleon", "atomic number",
    "mass number", "isotope", "radioactive", "radioactivity",
    "alpha decay", "beta decay", "gamma decay", "half-life",
    "decay constant", "binding energy", "mass defect",
    "fission", "fusion", "chain reaction", "critical mass",

    # Particle physics / 
    "particle", "elementary particle", "quark", "lepton", "electron",
    "muon", "tau", "neutrino", "photon", "gluon", "w boson",
    "z boson", "higgs boson", "standard model", "antimatter",
    "antiparticle", "annihilation", "pair production"
}

FLUID_MECHANICS_KEYWORDS = {
    # Fluid properties / 
    "fluid", "liquid", "gas", "density", "pressure", "buoyancy",
    "archimedes", "floating", "sinking", "specific gravity",
    "viscosity", "surface tension", "cohesion", "adhesion",
    "capillary", "meniscus",

    # Fluid statics / 
    "hydrostatic", "pascal's law", "hydraulic", "atmospheric pressure",
    "gauge pressure", "absolute pressure", "barometer", "manometer",

    # Fluid dynamics / 
    "flow", "streamline", "laminar flow", "turbulent flow",
    "reynolds number", "continuity equation", "bernoulli's equation",
    "venturi effect", "torricelli's theorem", "flow rate",
    "volume flow rate", "mass flow rate", "incompressible",
    "compressible", "viscous flow", "ideal fluid"
}

# Combine all physics keywords / 
PHYSICS_KEYWORDS = (
    MECHANICS_KEYWORDS | THERMODYNAMICS_KEYWORDS | ELECTROMAGNETISM_KEYWORDS |
    OPTICS_KEYWORDS | WAVES_KEYWORDS | MODERN_PHYSICS_KEYWORDS |
    FLUID_MECHANICS_KEYWORDS
)


# ============================================================
# CHEMISTRY KEYWORDS / 
# ============================================================

CHEMISTRY_KEYWORDS = {
    # General chemistry / 
    "atom", "molecule", "element", "compound", "mixture",
    "solution", "solvent", "solute", "concentration", "molarity",
    "molality", "mole", "molar mass", "avogadro's number",
    "stoichiometry", "limiting reagent", "excess reagent",
    "yield", "percent yield", "empirical formula", "molecular formula",

    # Chemical reactions / 
    "reaction", "reactant", "product", "catalyst", "enzyme",
    "activation energy", "endothermic", "exothermic", "enthalpy change",
    "combustion", "synthesis", "decomposition", "single replacement",
    "double replacement", "neutralization", "precipitation",

    # Acids and bases / 
    "acid", "base", "ph", "poh", "neutral", "acidic", "basic",
    "alkaline", "buffer", "titration", "indicator", "equivalence point",
    "end point", "strong acid", "weak acid", "conjugate",

    # Redox / 
    "oxidation", "reduction", "redox", "oxidizing agent",
    "reducing agent", "electron transfer", "oxidation number",
    "half reaction", "electrochemistry", "galvanic cell",
    "electrolytic cell", "electrode", "anode", "cathode",

    # Equilibrium / 
    "equilibrium", "equilibrium constant", "le chatelier",
    "reversible reaction", "rate", "rate law", "rate constant",
    "order of reaction", "kinetics", "activation energy"
}


# ============================================================
# ENGINEERING KEYWORDS / 
# ============================================================

ENGINEERING_KEYWORDS = {
    # Mechanical engineering / 
    "stress", "strain", "young's modulus", "shear modulus",
    "bulk modulus", "poisson's ratio", "yield strength",
    "ultimate strength", "elasticity", "plasticity", "fracture",
    "fatigue", "creep", "beam", "cantilever", "truss",

    # Electrical engineering / 
    "semiconductor", "diode", "transistor", "amplifier",
    "op-amp", "digital", "analog", "logic gate", "boolean",
    "flip-flop", "register", "counter", "multiplexer",
    "modulation", "demodulation", "filter", "oscillator",

    # Other engineering / 
    "efficiency", "optimization", "control system", "feedback",
    "transfer function", "stability", "damping", "response time"
}


# ============================================================
# COMBINED KEYWORD SETS / 
# ============================================================

# All academic keywords / 
ALL_ACADEMIC_KEYWORDS = (
    MATH_KEYWORDS | PHYSICS_KEYWORDS | CHEMISTRY_KEYWORDS | ENGINEERING_KEYWORDS
)

# Domain mapping / 
DOMAIN_KEYWORDS = {
    "mathematics": MATH_KEYWORDS,
    "algebra": ALGEBRA_KEYWORDS,
    "geometry": GEOMETRY_KEYWORDS,
    "trigonometry": TRIGONOMETRY_KEYWORDS,
    "calculus": CALCULUS_KEYWORDS,
    "statistics": STATISTICS_KEYWORDS,
    "number_theory": NUMBER_THEORY_KEYWORDS,

    "physics": PHYSICS_KEYWORDS,
    "mechanics": MECHANICS_KEYWORDS,
    "thermodynamics": THERMODYNAMICS_KEYWORDS,
    "electromagnetism": ELECTROMAGNETISM_KEYWORDS,
    "optics": OPTICS_KEYWORDS,
    "waves": WAVES_KEYWORDS,
    "modern_physics": MODERN_PHYSICS_KEYWORDS,
    "fluid_mechanics": FLUID_MECHANICS_KEYWORDS,

    "chemistry": CHEMISTRY_KEYWORDS,
    "engineering": ENGINEERING_KEYWORDS,
}


# ============================================================
# HELPER FUNCTIONS / 
# ============================================================

def get_keywords_by_domain(domain: str) -> set:
    """
    Get keywords for a specific domain.
    

    Args:
        domain: Domain name (e.g., 'mechanics', 'algebra')
                 'mechanics''algebra'

    Returns:
        Set of keywords for the domain
        
    """
    return DOMAIN_KEYWORDS.get(domain.lower(), set())


def get_all_keywords() -> set:
    """
    Get all academic keywords.
    

    Returns:
        Set of all keywords
        
    """
    return ALL_ACADEMIC_KEYWORDS


def identify_domains(text: str) -> dict:
    """
    Identify which academic domains are relevant to the given text.
    

    Args:
        text: Text to analyze
              

    Returns:
        Dictionary mapping domain names to match counts
        
    """
    text_lower = text.lower()
    words = set(text_lower.split())

    domain_matches = {}
    for domain_name, keywords in DOMAIN_KEYWORDS.items():
        matches = words & keywords
        if matches:
            domain_matches[domain_name] = {
                "count": len(matches),
                "keywords": list(matches)[:10]  # Limit to 10 keywords
            }

    return domain_matches


def extract_keywords_from_text(text: str, max_keywords: int = 10) -> list:
    """
    Extract academic keywords from text.
    

    This function filters out common stopwords and focuses on domain-specific
    technical terms.

    

    Args:
        text: Text to analyze
              
        max_keywords: Maximum number of keywords to return
                      

    Returns:
        List of extracted keywords
        
    """
    import re

    # Try to import stopwords, fallback to basic stopwords if module not available
    # 
    try:
        from .stopwords import get_all_stopwords
        stopwords = get_all_stopwords()
    except (ImportError, ValueError):
        # Fallback for when running as main script
        # 
        try:
            from stopwords import get_all_stopwords
            stopwords = get_all_stopwords()
        except ImportError:
            # Basic stopwords as last resort
            # 
            stopwords = {
                'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been',
                'of', 'in', 'to', 'for', 'with', 'on', 'at', 'from', 'by'
            }

    text_lower = text.lower()

    # Extract words from problem
    words = set(re.findall(r'\b[a-z]+\b', text_lower))

    # Filter out stopwords first, then find academic keywords
    # 
    words_filtered = words - stopwords

    # Find matching academic keywords
    # 
    extracted = list(words_filtered & ALL_ACADEMIC_KEYWORDS)

    # If too few keywords, add generic ones based on detected domains
    # 
    if len(extracted) < 2:
        domain_matches = identify_domains(text)
        if domain_matches:
            # Add most relevant domain name
            top_domain = max(domain_matches.items(), key=lambda x: x[1]["count"])
            extracted.append(top_domain[0])
        else:
            # Default fallback (but not stopwords like "problem", "solve")
            #  "problem""solve" 
            extracted.extend(["mathematics", "physics"])

    return extracted[:max_keywords]


# Example usage / 
if __name__ == "__main__":
    # Test keyword extraction / 
    test_problems = [
        "An object with mass 10 kg starts from rest. A force of 50 N acts on it.",
        "Find the derivative of f(x) = x^2 + 3x + 5",
        "A circuit contains a resistor of 100 ohms and a capacitor of 10 microfarads.",
        "Calculate the area of a circle with radius 5 meters."
    ]

    print("="*70)
    print("Domain Keywords Test / ")
    print("="*70)

    for i, problem in enumerate(test_problems, 1):
        print(f"\nProblem {i}: {problem}")
        print(f" {i}: {problem}\n")

        # Extract keywords
        keywords = extract_keywords_from_text(problem)
        print(f"Extracted keywords: {keywords}")
        print(f": {keywords}")

        # Identify domains
        domains = identify_domains(problem)
        print(f"\nRelevant domains: {list(domains.keys())}")
        print(f": {list(domains.keys())}")

        for domain, info in domains.items():
            print(f"  - {domain}: {info['count']} matches")
            print(f"    Sample keywords: {info['keywords'][:5]}")

        print("-"*70)

    print(f"\n\nTotal keywords in database: {len(ALL_ACADEMIC_KEYWORDS)}")
    print(f": {len(ALL_ACADEMIC_KEYWORDS)}")

    print(f"\nKeywords by domain / :")
    for domain, keywords in DOMAIN_KEYWORDS.items():
        print(f"  - {domain}: {len(keywords)} keywords")
