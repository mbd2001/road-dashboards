import argparse

import yaml


def parse_args(args=None):
    parser = argparse.ArgumentParser(description="create envs from recipe.yaml")
    parser.add_argument("--env_type", help="User for Artifactory", required=True, choices=["run", "test"])
    parser.add_argument("--proj_name", help="Project Name", required=True)
    parser.add_argument(
        "--recipe_path",
        help="boa recipe file path - containing the project dependencies.",
        required=False,
        default="boa.recipe/recipe.yaml",
    )
    parser.add_argument("--out_env_yaml", help="file path for output yaml file", required=False, default=None)
    args = parser.parse_args()
    return args


def create_env_yaml(proj_name, recipe_path, out_env_yaml, env_type):
    """
    Creates env yaml file out of boa recipe.
    """
    with open(recipe_path) as f:
        recipe_yaml = yaml.safe_load(f)

    env_yaml_dict = {}
    env_yaml_dict["name"] = proj_name
    env_yaml_dict["dependencies"] = recipe_yaml["requirements"]["run"]
    if env_type == "test":
        env_yaml_dict["channels"] = ["conda-forge", "me-conda-dev-local", "comet_ml"]
        env_yaml_dict["dependencies"] += recipe_yaml["test"]["requires"]

    out_env_yaml = out_env_yaml or f"/tmp/{proj_name}.{env_type}.yml"
    with open(out_env_yaml, "w") as f:
        yaml.dump(env_yaml_dict, f, indent=2)


def main():
    args = parse_args()
    create_env_yaml(
        proj_name=args.proj_name,
        recipe_path=args.recipe_path,
        out_env_yaml=args.out_env_yaml,
        env_type=args.env_type,
    )


if __name__ == "__main__":
    main()
