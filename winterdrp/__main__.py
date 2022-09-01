#!/usr/bin/env python
import argparse
import os
import sys
import logging
from winterdrp.pipelines import get_pipeline, Pipeline
from winterdrp.paths import raw_img_sub_dir
from astropy.time import Time
from astropy import units as u
from winterdrp.monitor.base_monitor import Monitor
from winterdrp.paths import base_raw_dir
from datetime import datetime

logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(
    description="winterdrp: An automated image reduction pipeline, developed for WINTER"
)

ln = Time.now() - 1. * u.day
parser.add_argument(
    "-n",
    "--night",
    default=None,
    help="Sub-directory to use in the data directory"
)
parser.add_argument(
    "-p",
    "--pipeline",
    default="summer",
    help="Pipeline to be used"
)
parser.add_argument(
    "-c",
    "--config",
    default=None,
    help="Pipeline configuration to be used"
)
parser.add_argument(
    "--logfile",
    default=None,
    help="If a path is passed, all logs will be written to this file."
)
parser.add_argument(
    "--level",
    default="DEBUG",
    help="Python logging level"
)
parser.add_argument(
    "-b",
    "--batch",
    default=None,
    help="Only process a specific image batch"
)
parser.add_argument(
    '--download',
    help='Download images from server',
    action='store_true',
    default=False
)

parser.add_argument(
    "-m",
    "--monitor",
    action="store_true",
    default=False
)
parser.add_argument(
    "--emailrecipients",
    default=None,
    help='Spaceless comma-separated values of email recipients',
)
parser.add_argument(
    "--emailsender",
    default=None,
    help='One email sender',
)
parser.add_argument(
    "--emailwaithours",
    default=24.,
    help='Time, in hours, to wait before sending a summary email',
)
parser.add_argument(
    "--maxwaithours",
    default=48.,
    help='Time, in hours, to wait before ceasing monitoring for new images',
)
parser.add_argument(
    "--rawdir",
    default=raw_img_sub_dir,
    help="Subdirectory to look in for raw images of a given night"
)

args = parser.parse_args()

if args.download:

    Pipeline.pipelines[args.pipeline.lower()].download_raw_images_for_night(
        night=args.night
    )

    logger.info("Download complete")

if args.monitor:

    if args.emailrecipients is not None:
        email_recipients = args.emailrecipients.split(",")
    else:
        email_recipients = None

    night = args.night
    if night is None:
        night = str(datetime.now()).split(" ")[0].replace("-", "")

    monitor = Monitor(
        pipeline=args.pipeline,
        night=night,
        realtime_configurations=["realtime"],
        log_level=args.level,
        max_wait_hours=args.maxwaithours,
        email_wait_hours=args.emailwaithours,
        email_sender=args.emailsender,
        email_recipients=email_recipients,
        raw_dir=args.rawdir
    )
    monitor.process_realtime()

else:

    # Set up logging

    log = logging.getLogger("winterdrp")

    if args.logfile is None:
        handler = logging.StreamHandler(sys.stdout)
    else:
        handler = logging.FileHandler(args.logfile)

    formatter = logging.Formatter('%(name)s [l %(lineno)d] - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    log.addHandler(handler)
    log.setLevel(args.level)

    night = args.night
    if night is None:
        night = str(ln).split(" ")[0].replace("-", "")

    pipe = get_pipeline(
        args.pipeline,
        selected_configurations=args.config,
        night=night,
    )

    pipe.reduce_images([[[], []]], catch_all_errors=True)

    logger.info('End of winterdrp execution')
