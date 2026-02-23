from jubapi.policy import PolicyManager

def test_policy():
    pm = PolicyManager()
    raw_policy = pm.load_from_yaml("/home/nacho/Programming/Python/oca_api/data/policy.yml")
    print(raw_policy)
