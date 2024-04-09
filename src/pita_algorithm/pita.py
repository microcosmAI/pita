import logging
import os
import sys
import random
import typer
import warnings
import numpy as np
from typing import Union
from importlib_resources import files

# Add parent folder of builder.py to python path
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pita_algorithm.base.assembler import Assembler
from pita_algorithm.utils.json_exporter import JSONExporter
from pita_algorithm.utils.xml_exporter import XMLExporter
from pita_algorithm.utils.config_reader import ConfigReader
from pita_algorithm.utils.logger import Logger


class PITA:
    """Main class to run the PITA algorithm."""

    def run(
        self,
        random_seed: Union[int, None] = None,
        config_path: Union[str, None] = None,
        xml_dir: Union[str, None] = None,
        export_path: Union[str, None] = None,
        plot: Union[bool, None] = None,
    ):
        """Run pita_algorithm to create xml-file containing objects specified in config file.
        Objects are given as xml by the user.

        Parameters:
            random_seed (Union[int, None]): Seed for reproducibility
            config_path (Union[str, None]): Path to where the yaml file is located
            xml_dir (Union[str, None]): Folder where all xml files are located
            export_path (Union[str, None]): Path (including file name but excluding extension) to export to
            plot (Union[bool, None]): True for plotting, False if not
        """
        if config_path is None:
            print("files: ", files("pita_algorithm.examples.config_files"))
            config_path = files("pita_algorithm.examples.config_files").joinpath(
                "complex-config.yml"
            )
            warnings.warn(
                "config path not specified; running with default directory in examples"
            )
        if xml_dir is None:
            xml_dir = files("pita_algorithm.examples").joinpath("xml_objects")
            warnings.warn(
                "xml directory not specified; running with default directory in examples"
            )
        if export_path is None:
            export_path = "export/test"
            warnings.warn(
                "export path not specified; running with default directory in export and filename 'test'"
            )

        config = ConfigReader.execute(config_path=config_path)
        logger = logging.getLogger()

        # Set random seed
        if (
            random_seed is not None
            and "random_seed" in config["Environment"]
            and config["Environment"]["random_seed"] is not None
        ):
            logger.info(
                "Two seeds were specified (call argument to PITA.run() and in level config file). Using seed from the call."
            )
            logger.info(f"Setting random seed to {random_seed}")
            np.random.seed(random_seed)
            random.seed(random_seed)
        elif random_seed is not None:
            np.random.seed(random_seed)
            random.seed(random_seed)
        elif (
            "random_seed" in config["Environment"]
            and config["Environment"]["random_seed"] is not None
        ):
            random_seed = config["Environment"]["random_seed"]
            logger.info(f"Setting random seed to {random_seed}")
            np.random.seed(random_seed)
            random.seed(random_seed)

        # Assemble world
        environment, areas = Assembler(
            config_file=config, xml_dir=xml_dir, plot=plot
        ).assemble_world()

        # Export to xml and json
        XMLExporter.to_xml(
            xml_string=environment.mjcf_model.to_xml_string(),
            export_path=export_path,
        )
        JSONExporter.export(
            export_path=export_path,
            config=config,
            environment=environment,
            areas=areas,
        )


def main(
    random_seed: int = typer.Option(default=None, help="Pass seed."),
    config_path: str = typer.Option(
        default="complex-config.yml",
        help="Specify path to config yml.",
    ),
    xml_dir: str = typer.Option(
        default="examples/xml_objects", help="Specify path to xml files."
    ),
    export_path: str = typer.Option(
        default="export/test", help="Specify path to output directory."
    ),
    plot: bool = typer.Option(default=False, help="Set to True to enable plots."),
):
    Logger.initialize_logger()
    logger = logging.getLogger()
    logger.info(
        f"Running PITA with following parameters: \n" + "-" * 50 + "\n"
        f"random_seed: '{random_seed}' \n"
        f"config_path: '{config_path}' \n"
        f"xml_dir: '{xml_dir}' \n"
        f"export_path: '{export_path}' \n"
        f"plot: '{plot}' \n" + "-" * 50,
    )
    PITA().run(
        random_seed=random_seed,
        config_path=config_path,
        xml_dir=xml_dir,
        export_path=export_path,
        plot=plot,
    )
    logger.info("Done.")


if __name__ == "__main__":
    typer.run(main)