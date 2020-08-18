import logging
import os
import sys

import numpy as np

from hexrd import config
from hexrd import constants as cnst
from hexrd import instrument
from hexrd.fitgrains import fit_grains
from hexrd.transforms import xfcapi


descr = 'Extracts G vectors, grain position and strain'
example = """
examples:
    hexrd fit-grains configuration.yml
"""


def configure_parser(sub_parsers):
    p = sub_parsers.add_parser('fit-grains', description=descr, help=descr)
    p.add_argument(
        'yml', type=str,
        help='YAML configuration file'
        )
    p.add_argument(
        '-g', '--grains', type=str, default=None,
        help="comma-separated list of IDs to refine, defaults to all"
        )
    p.add_argument(
        '-q', '--quiet', action='store_true',
        help="don't report progress in terminal"
        )
    p.add_argument(
        '-c', '--clean', action='store_true',
        help='overwrites existing analysis, uses initial orientations'
        )
    p.add_argument(
        '-f', '--force', action='store_true',
        help='overwrites existing analysis'
        )
    p.add_argument(
        '-p', '--profile', action='store_true',
        help='runs the analysis with cProfile enabled',
        )
    p.set_defaults(func=execute)


def write_results(fit_results, cfg, grains_filename='grains.out'):
    instr = cfg.instrument.hedm

    # make output directories
    if not os.path.exists(cfg.analysis_dir):
        os.mkdir(cfg.analysis_dir)
        for det_key in instr.detectors:
            os.mkdir(os.path.join(cfg.analysis_dir, det_key))
    else:
        # make sure panel dirs exist under analysis dir
        for det_key in instr.detectors:
            if not os.path.exists(os.path.join(cfg.analysis_dir, det_key)):
                os.mkdir(os.path.join(cfg.analysis_dir, det_key))

    gw = instrument.GrainDataWriter(
        os.path.join(cfg.analysis_dir, grains_filename)
    )
    for fit_result in fit_results:
        gw.dump_grain(*fit_result)
    gw.close()


def execute(args, parser):
    # load the configuration settings
    cfgs = config.open(args.yml)

    # configure logging to the console:
    log_level = logging.DEBUG if args.debug else logging.INFO
    if args.quiet:
        log_level = logging.ERROR
    logger = logging.getLogger('hexrd')
    logger.setLevel(log_level)
    ch = logging.StreamHandler()
    ch.setLevel(logging.CRITICAL if args.quiet else log_level)
    cf = logging.Formatter('%(asctime)s - %(message)s', '%y-%m-%d %H:%M:%S')
    ch.setFormatter(cf)
    logger.addHandler(ch)

    # if find-orientations has not already been run, do so:
    quats_f = os.path.join(
        cfgs[0].working_dir,
        'accepted_orientations_%s.dat' % cfgs[0].analysis_id
        )
    if os.path.exists(quats_f):
        try:
            qbar = np.loadtxt(quats_f).T
        except(IOError):
            raise(RuntimeError,
                  "error loading indexing results '%s'" % quats_f)
    else:
        logger.info("Missing %s, running find-orientations", quats_f)
        logger.removeHandler(ch)
        from hexrd.findorientations import find_orientations
        results = find_orientations(cfgs[0])
        qbar = results['qbar']
        logger.addHandler(ch)

    logger.info('=== begin fit-grains ===')

    clobber = args.force or args.clean
    for cfg in cfgs:
        # prepare the analysis directory
        if os.path.exists(cfg.analysis_dir) and not clobber:
            logger.error(
                'Analysis "%s" at %s already exists.'
                ' Change yml file or specify "force"',
                cfg.analysis_name, cfg.analysis_dir
                )
            sys.exit()

        # make output directories
        instr = cfg.instrument.hedm
        if not os.path.exists(cfg.analysis_dir):
            os.makedirs(cfg.analysis_dir)
            for det_key in instr.detectors:
                os.mkdir(os.path.join(cfg.analysis_dir, det_key))
        else:
            # make sure panel dirs exist under analysis dir
            for det_key in instr.detectors:
                if not os.path.exists(os.path.join(cfg.analysis_dir, det_key)):
                    os.mkdir(os.path.join(cfg.analysis_dir, det_key))

        logger.info('*** begin analysis "%s" ***', cfg.analysis_name)

        # configure logging to file for this particular analysis
        logfile = os.path.join(
            cfg.working_dir,
            cfg.analysis_name,
            'fit-grains.log'
            )
        fh = logging.FileHandler(logfile, mode='w')
        fh.setLevel(log_level)
        ff = logging.Formatter(
                '%(asctime)s - %(name)s - %(message)s',
                '%m-%d %H:%M:%S'
                )
        fh.setFormatter(ff)
        logger.info("logging to %s", logfile)
        logger.addHandler(fh)

        if args.profile:
            import cProfile as profile
            import pstats
            from io import StringIO

            pr = profile.Profile()
            pr.enable()

        grains_filename = os.path.join(
            cfg.analysis_dir, 'grains.out'
        )

        # some conditions for arg handling
        existing_analysis = os.path.exists(grains_filename)
        new_with_estimate = not existing_analysis \
            and cfg.fit_grains.estimate is not None
        new_without_estimate = not existing_analysis \
            and cfg.fit_grains.estimate is None
        force_with_estimate = args.force \
            and cfg.fit_grains.estimate is not None
        force_without_estimate = args.force and cfg.fit_grains.estimate is None

        # handle args
        if args.clean or force_without_estimate or new_without_estimate:
            # need accepted orientations from indexing in this case
            if args.clean:
                logger.info(
                    "'clean' specified; ignoring estimate and using default"
                )
            elif force_without_estimate:
                logger.info(
                    "'force' option specified, but no initial estimate; "
                    + "using default"
                )
            try:
                gw = instrument.GrainDataWriter(grains_filename)
                for i_g, q in enumerate(qbar.T):
                    phi = 2*np.arccos(q[0])
                    n = xfcapi.unitRowVector(q[1:])
                    grain_params = np.hstack(
                        [phi*n, cnst.zeros_3, cnst.identity_6x1]
                    )
                    gw.dump_grain(int(i_g), 1., 0., grain_params)
                gw.close()
            except(IOError):
                raise(RuntimeError,
                      "indexing results '%s' not found!"
                      % 'accepted_orientations_' + cfg.analysis_id + '.dat')
        elif force_with_estimate or new_with_estimate:
            grains_filename = cfg.fit_grains.estimate
        elif existing_analysis and not (clean or force):
            raise(RuntimeError,
                  "fit results '%s' exist, " % grains_filename
                  + "but --clean or --force options not specified")

        grains_table = np.loadtxt(grains_filename, ndmin=2)

        # process the data
        gid_list = None
        if args.grains is not None:
            gid_list = [int(i) for i in args.grains.split(',')]
            pass

        cfg.fit_grains.qbar = qbar
        fit_results = fit_grains(
            cfg,
            grains_table,
            show_progress=not args.quiet,
            ids_to_refine=gid_list,
            )

        if args.profile:
            pr.disable()
            s = StringIO.StringIO()
            ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
            ps.print_stats(50)
            logger.info('%s', s.getvalue())

        # stop logging for this particular analysis
        fh.flush()
        fh.close()
        logger.removeHandler(fh)

        logger.info('*** end analysis "%s" ***', cfg.analysis_name)

        write_results(fit_results, cfg)

    logger.info('=== end fit-grains ===')
    # stop logging to the console
    ch.flush()
    ch.close()
    logger.removeHandler(ch)
