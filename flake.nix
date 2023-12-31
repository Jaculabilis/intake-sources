{
  description = "intake feed sources";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/23.05";

  outputs = { self, nixpkgs }:
  let
    system = "x86_64-linux";
  in {
    packages.${system} = let
      pkgs = (import nixpkgs {
        inherit system;
        overlays = [ self.overlays.default ];
      });
    in {
      default = pkgs.intakeSources;
      inherit (pkgs) intake-rss intake-reddit intake-hackernews intake-echo intake-praw;
    };

    devShells.${system} = {
      python = let
        pkgs = nixpkgs.legacyPackages.${system};
        pythonEnv = pkgs.python38.withPackages (pypkgs: with pypkgs; [ black feedparser praw ]);
      in pkgs.mkShell {
        packages = [ pythonEnv ];
        shellHook = ''
          PS1="(python) $PS1"
        '';
      };
    };

    overlays.default = final: prev: let
      pythonPackage = name: path: deps: final.python38Packages.buildPythonPackage {
        inherit name;
        src = builtins.path { inherit name path; };
        format = "pyproject";
        propagatedBuildInputs = [ final.python38Packages.setuptools ] ++ deps;
      };
    in
    {
      intakeSources = final.symlinkJoin {
        name = "intake-sources";
        paths = [
          final.intake-rss
          final.intake-reddit
          final.intake-hackernews
          final.intake-echo
          final.intake-praw
        ];
      };
      intake-rss = pythonPackage "intake-rss" ./intake-rss [ final.python38Packages.feedparser ];
      intake-reddit = pythonPackage "intake-reddit" ./intake-reddit [];
      intake-hackernews = pythonPackage "intake-hackernews" ./intake-hackernews [];
      intake-echo = pythonPackage "intake-echo" ./intake-echo [];
      intake-praw = pythonPackage "intake-praw" ./intake-praw [ final.python38Packages.praw ];
    };

    nixosModules.default = {
      nixpkgs.overlays = [ self.overlays.default ];
    };
  };
}

