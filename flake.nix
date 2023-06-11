{
  description = "intake feed sources";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/22.11";

  outputs = { self, nixpkgs }:
  let
    system = "x86_64-linux";
    pkgs = nixpkgs.legacyPackages.${system};
  in {
    packages.${system} = {
      intake-rss = pkgs.python38Packages.buildPythonPackage {
        name = "intake-rss";
        src = builtins.path { path = ./intake-rss; name = "intake-rss"; };
        format = "pyproject";
        propagatedBuildInputs = with pkgs.python38Packages; [ feedparser setuptools ];
      };
    };

    devShells.${system} = {
      intake-rss = let
        pythonEnv = pkgs.python38.withPackages (pypkgs: with pypkgs; [ black feedparser ]);
      in pkgs.mkShell {
        packages = [ pythonEnv ];
        shellHook = ''
          PS1="(intake-rss) $PS1"
        '';
      };
    };
  };
}

