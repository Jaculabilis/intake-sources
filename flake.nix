{
  description = "intake feed sources";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/23.05";

  outputs = { self, nixpkgs }:
  let
    system = "x86_64-linux";
    pkgs = nixpkgs.legacyPackages.${system};
    pypkgs = pkgs.python38Packages;
    pythonPackage = name: path: deps: pypkgs.buildPythonPackage {
      inherit name;
      src = builtins.path { inherit name path; };
      format = "pyproject";
      propagatedBuildInputs = [ pypkgs.setuptools ] ++ deps;
    };
  in {
    packages.${system} = {
      default = pkgs.symlinkJoin {
        name = "intake-sources";
        paths = [
          self.packages.${system}.intake-rss
          self.packages.${system}.intake-reddit
          self.packages.${system}.intake-hackernews
        ];
      };
      intake-rss = pythonPackage "intake-rss" ./intake-rss [ pypkgs.feedparser ];
      intake-reddit = pythonPackage "intake-reddit" ./intake-reddit [];
      intake-hackernews = pythonPackage "intake-hackernews" ./intake-hackernews [];
    };

    devShells.${system} = {
      python = let
        pythonEnv = pkgs.python38.withPackages (pypkgs: with pypkgs; [ black feedparser ]);
      in pkgs.mkShell {
        packages = [ pythonEnv ];
        shellHook = ''
          PS1="(python) $PS1"
        '';
      };
    };
  };
}

