""" PANEL NUMBERS AND PANEL PROPERTIES

The PANEL_DICT is built up in stages using various other dictionaries to reduce
repetition

- SNP does not have R numbers (test_number) as it is an identity check for the
    GMS SMS
- Panels for WES (analysed in Congenica), SWIFT and TSO500 (analysed in QCII),
    and ArcherDX (analysed in Archer software), are applied at the point of
    analysis, so R and M numbers (test_number) for these are not listed below.
    These pan numbers do not necessarily refer to bed files but rather project
    configuration (e.g. DNAnexus instances, project layout etc.


Dictionary keys and values are as follows:

    pipeline:                     Name of pipeline
    panel_name:                   Name of capture panel
    capture_pan_num:              Pan number of capture panel bedfile (used for RPKM).
                                  False if RPKM not run
    hsmetrics_bedfile:            bedfile filename, or None
    sambamba_bedfile:             bedfile filename, or None
    variant_calling_bedfile:      bedfile filename, or None
    capture_type:                 Amplicon or Hybridisation
    multiqc_coverage_level:       Value
    clinical_coverage_depth:      Value, or False. Used as input for sambamba
                                  and mpileup
    coverage_min_basecall_qual:   Value or False. Sambamba minimum base quality
    coverage_min_mapping_qual:    False. Sambamba minimum mapping quality
    masked_reference:             projectid:fileid, or False if not required
    throughput:                   'high' or 'low', or False if unspecified
    test_number:                  R or M number, or false if no specific number
    congenica_project:            False = no upload. Number = normal. SFTP =
                                  sftp upload
    congenica_credentials:        'Viapath' or 'StG'. False = congenica app not
                                  used
    congenica_IR_template:        'priority' or 'non-priority'. False =
                                  congenica app not used
    polyedge:                     False if app not required, subdictionary
                                  containing app inputs if it is required
    dry_lab_only:                 Used to determine whether to include the TSO
                                  pan number in the duty_csv pan number list
    FH:                           False if app not required, bed file if it is
    drylab_dnanexus_id:           False if not required to share with other
                                  users, user ID string if needs sharing
"""
import config.ad_config as ad_config  # Import ad_config file

# TODO check which variables are used by trend script and whether they are
# affected
# TODO look into whether the 100X maximum coverage for multiqc can be raised
# for compatibility with TSO500

PIPE_HAPLOTYPE_CALLER_PADDING = 0

# Mokapipe FH_PRS BED file
FH_PRS_BEDFILE = f"{ad_config.BEDFILE_FOLDER}Pan4909.bed"

POLYEDGE_INPUTS = {
    "MSH2": {
        "gene": "MSH2",
        "chrom": 2,
        "poly_start": 47641559,
        "poly_end": 47641586,
    }
}

CONGENICA_CREDENTIALS = {
    "viapath": {
        "congenica_credentials": "Viapath",
        "congenica_IR_template": "priority",
    },
    "stg": {
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
    },
}

# Default dictionary upon which the panel dictionary is built -
# values are replaced within subsequent dictionaries
DEFAULT_DICT = {
    "panel_name": False,
    "pipeline": False,
    "capture_pan_num": False,
    "hsmetrics_bedfile": False,
    "sambamba_bedfile": False,
    "variant_calling_bedfile": False,
    "capture_type": False,
    "multiqc_coverage_level": False,
    "clinical_coverage_depth": False,
    "coverage_min_basecall_qual": False,
    "coverage_min_mapping_qual": False,
    "masked_reference": False,
    "throughput": False,
    "test_number": False,
    "congenica_project": False,
    "congenica_credentials": False,
    "congenica_IR_template": False,
    "polyedge": False,
    "FH": False,
    "dry_lab_only": False,
    "drylab_dnanexus_id": False,
}


# Dictionary containing values that apply across the capture
CAPTURE_PANEL_DICT = {
    "vcp1": {
        **DEFAULT_DICT,
        "panel_name": "vcp1",
        "pipeline": "pipe",
        "capture_pan_num": "Pan4399",
        "hsmetrics_bedfile": "Pan4397data.bed",
        "sambamba_bedfile": f"{ad_config.BEDFILE_FOLDER}Pan4397dataSambamba.bed",
        "variant_calling_bedfile": "Pan4398data.bed",
        "capture_type": "Hybridisation",
        "multiqc_coverage_level": 30,
        "clinical_coverage_depth": 30,
        "coverage_min_basecall_qual": 10,
        "coverage_min_mapping_qual": 20,
    },
    "vcp2": {
        **DEFAULT_DICT,
        "panel_name": "vcp2",
        "pipeline": "pipe",
        "capture_pan_num": "Pan5109",
        "hsmetrics_bedfile": "Pan5123data.bed",
        "sambamba_bedfile": f"{ad_config.BEDFILE_FOLDER}Pan5123dataSambamba.bed",
        "variant_calling_bedfile": "Pan5119data.bed",
        "capture_type": "Hybridisation",
        "multiqc_coverage_level": 30,
        "clinical_coverage_depth": 30,
        "coverage_min_basecall_qual": 10,
        "coverage_min_mapping_qual": 20,
    },
    "vcp3": {
        **DEFAULT_DICT,
        "panel_name": "vcp3",
        "pipeline": "pipe",
        "capture_pan_num": "Pan4362",
        "hsmetrics_bedfile": "Pan4995data.bed",
        "sambamba_bedfile": f"{ad_config.BEDFILE_FOLDER}Pan4995dataSambamba.bed",
        "variant_calling_bedfile": "Pan4995data.bed",
        "capture_type": "Hybridisation",
        "multiqc_coverage_level": 30,
        "clinical_coverage_depth": 30,
        "coverage_min_basecall_qual": 10,
        "coverage_min_mapping_qual": 20,
    },
    "lrpcr": {
        **DEFAULT_DICT,
        "panel_name": "lrpcr",
        "pipeline": "pipe",
        "hsmetrics_bedfile": "Pan4967_reference.bed",  # LRPCR amplicon BEDfile
        "sambamba_bedfile": f"{ad_config.BEDFILE_FOLDER}Pan5018dataSambamba.bed",
        "variant_calling_bedfile": "Pan4767data.bed",
        "capture_type": "Amplicon",
        "multiqc_coverage_level": 30,
        "clinical_coverage_depth": 30,
        "coverage_min_basecall_qual": 10,
        "coverage_min_mapping_qual": 20,
        "masked_reference": ad_config.NEXUS_IDS["FILES"]["masked_reference"],
    },
    "swift_57g": {
        **DEFAULT_DICT,
        "panel_name": "swift_57g",
        "pipeline": "amp",
        "hsmetrics_bedfile": "Pan4082.bed",
        "sambamba_bedfile": f"{ad_config.BEDFILE_FOLDER}Pan4082Sambamba.bed",
        "capture_type": "Amplicon",
        "clinical_coverage_depth": 600,  # Only found in mokamp command
        "multiqc_coverage_level": 100,
    },
    "swift_egfr": {
        **DEFAULT_DICT,
        "panel_name": "swift_egfr",
        "pipeline": "amp",
        "sambamba_bedfile": f"{ad_config.BEDFILE_FOLDER}Pan4081Sambamba.bed",
        "hsmetrics_bedfile": "Pan4081.bed",
        "capture_type": "Amplicon",
        "clinical_coverage_depth": 600,  # Only found in mokamp command
        "multiqc_coverage_level": 100,
    },
    "snp": {
        **DEFAULT_DICT,
        "panel_name": "snp",
        "pipeline": "snp",
        "variant_calling_bedfile": "Pan4009.bed",
        "capture_type": "Hybridisation",
        "multiqc_coverage_level": 30,
    },
    "wes": {
        **DEFAULT_DICT,
        "panel_name": "wes",
        "pipeline": "wes",
        "sambamba_bedfile": f"{ad_config.BEDFILE_FOLDER}Pan493dataSambamba.bed",
        "hsmetrics_bedfile": "Twist_Exome_RefSeq_CCDS_v1.2_targets.bed",
        "capture_type": "Hybridisation",
        "multiqc_coverage_level": 20,
    },
    "wes_eb": {
        **DEFAULT_DICT,
        "panel_name": "wes_eb",
        "pipeline": "wes",
        "sambamba_bedfile": f"{ad_config.BEDFILE_FOLDER}Pan493dataSambamba.bed",
        "hsmetrics_bedfile": "Twist_Exome_RefSeq_CCDS_v1.2_targets.bed",
        "capture_type": "Hybridisation",
        "multiqc_coverage_level": 20,
    },
    "archerdx": {
        **DEFAULT_DICT,
        "panel_name": "archerdx",
        "pipeline": "archerdx",
        "capture_type": "Hybridisation",
        "multiqc_coverage_level": 30,  # We don't align for Archer
    },
    "tso500": {
        **DEFAULT_DICT,
        "panel_name": "tso500",
        "pipeline": "tso500",
        "sambamba_bedfile": f"{ad_config.BEDFILE_FOLDER}Pan4969dataSambamba.bed",
        "capture_type": "Hybridisation",
        "clinical_coverage_depth": 100,
        "multiqc_coverage_level": 100,
        "coverage_min_basecall_qual": 25,
        "coverage_min_mapping_qual": 30,
    },
}

# Dictionary containing pan number specific settings, arranged by workflow name
# These incorporate the capture dictionary settings and build upon them
PANEL_DICT = {
    "Pan4009": {  # SNP
        **CAPTURE_PANEL_DICT["snp"],
    },
    "Pan2835": {  # TWIST WES (Viapath)
        **CAPTURE_PANEL_DICT["wes"],
        "congenica_project": "SFTP",
    },
    "Pan4940": {  # TWIST WES for EB lab (Viapath)
        **CAPTURE_PANEL_DICT["wes_eb"],
        "congenica_project": "4697",
        "congenica_credentials": "Viapath",
        "congenica_IR_template": "priority",
    },
    **dict.fromkeys(
        [
            "Pan4396",  # ArcherDx (Synnovis)
            "Pan5113",  # ArcherDx (BSPS)
            "Pan5115",  # ArcherDx (Control)
        ],
        {
            **CAPTURE_PANEL_DICT["archerdx"],
        },
    ),
    "Pan4081": {  # SWIFT EGFR (Viapath)
        **CAPTURE_PANEL_DICT["swift_egfr"],
    },
    "Pan4082": {  # SWIFT 57G (Viapath)
        **CAPTURE_PANEL_DICT["swift_57g"],
    },
    "Pan4969": {  # TSO500 no UTRs. TERT promoter
        **CAPTURE_PANEL_DICT["tso500"],
        "throughput": "low",
    },
    "Pan5085": {  # TSO500 High throughput Synnovis. no UTRs. TERT promoter
        **CAPTURE_PANEL_DICT["tso500"],
        "throughput": "high",
    },
    "Pan5112": {  # TSO500 High throughput BSPS. no UTRs. TERT promoter
        **CAPTURE_PANEL_DICT["tso500"],
        "throughput": "high",
        "dry_lab_only": True,
        "drylab_dnanexus_id": "BSPS_MD",
    },
    "Pan5114": {  # TSO500 High throughput Control. no UTRs. TERT promoter
        **CAPTURE_PANEL_DICT["tso500"],
        "throughput": "high",
        "drylab_dnanexus_id": "BSPS_MD",
    },
    "Pan5007": {  # LRPCR R207 - PMS2 (Viapath)
        **CAPTURE_PANEL_DICT["lrpcr"],
        **CONGENICA_CREDENTIALS["viapath"],
        "test_number": "R207",
        "congenica_project": 9986,
    },
    "Pan5008": {  # LRPCR R207 - PMS2 (STG)
        **CAPTURE_PANEL_DICT["lrpcr"],
        **CONGENICA_CREDENTIALS["stg"],
        "test_number": "R207",
        "congenica_project": 10010,
    },
    "Pan5009": {  # LRPCR R208 - CHEK2 (Viapath)
        **CAPTURE_PANEL_DICT["lrpcr"],
        **CONGENICA_CREDENTIALS["viapath"],
        "test_number": "R208",
        "congenica_project": 9984,
    },
    "Pan5010": {  # LRPCR R208 - CHEK2 (STG)
        **CAPTURE_PANEL_DICT["lrpcr"],
        **CONGENICA_CREDENTIALS["stg"],
        "test_number": "R208",
        "congenica_project": 10009,
    },
    "Pan5011": {  # LRPCR R210 - PMS2 (Viapath)
        **CAPTURE_PANEL_DICT["lrpcr"],
        **CONGENICA_CREDENTIALS["viapath"],
        "test_number": "R210",
        "congenica_project": 9981,
    },
    "Pan5012": {  # LRPCR R210 - PMS2 (STG)
        **CAPTURE_PANEL_DICT["lrpcr"],
        "test_number": "R210",
        "congenica_project": 10042,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
    },
    "Pan5013": {  # LRPCR R211 - PMS2 (Viapath)
        **CAPTURE_PANEL_DICT["lrpcr"],
        **CONGENICA_CREDENTIALS["viapath"],
        "test_number": "R211",
        "congenica_project": 9982,
    },
    "Pan5014": {  # LRPCR R211 - PMS2 (STG)
        **CAPTURE_PANEL_DICT["lrpcr"],
        "test_number": "R211",
        "congenica_project": 10042,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
    },
    "Pan5015": {  # LRPCR R71 - SMN1 (Viapath)
        **CAPTURE_PANEL_DICT["lrpcr"],
        **CONGENICA_CREDENTIALS["viapath"],
        "test_number": "R71",
        "congenica_project": 9547,
    },
    "Pan5016": {  # LRPCR R239 - IKBKG (Viapath)
        **CAPTURE_PANEL_DICT["lrpcr"],
        **CONGENICA_CREDENTIALS["viapath"],
        "test_number": "R239",
        "congenica_project": 9985,
    },
    "Pan4119": {  # VCP1 R134 - FH small panel (Viapath)
        **CAPTURE_PANEL_DICT["vcp1"],
        **CONGENICA_CREDENTIALS["viapath"],
        "test_number": "R134",
        "congenica_project": 4664,
        "FH": FH_PRS_BEDFILE,
    },
    "Pan4121": {  # VCP1 R184 - CF (Viapath)
        **CAPTURE_PANEL_DICT["vcp1"],
        **CONGENICA_CREDENTIALS["viapath"],
        "test_number": "R184",
        "congenica_project": 4862,
    },
    "Pan4122": {  # VCP1 R25 - FGFR (Viapath)
        **CAPTURE_PANEL_DICT["vcp1"],
        **CONGENICA_CREDENTIALS["viapath"],
        "test_number": "R25",
        "congenica_project": 5291,
    },
    "Pan4125": {  # VCP1 R73 - DMD (Viapath)
        **CAPTURE_PANEL_DICT["vcp1"],
        **CONGENICA_CREDENTIALS["viapath"],
        "test_number": "R73",
        "congenica_project": 4861,
    },
    "Pan4126": {  # VCP1 R337 - CADASIL (Viapath)
        **CAPTURE_PANEL_DICT["vcp1"],
        **CONGENICA_CREDENTIALS["viapath"],
        "test_number": "R337",
        "congenica_project": 4865,
    },
    "Pan4974": {  # VCP1 R112 - Molecular Haemostasis (Viapath)
        **CAPTURE_PANEL_DICT["vcp1"],
        **CONGENICA_CREDENTIALS["viapath"],
        "test_number": "R112",
        "congenica_project": 4699,
    },
    "Pan4975": {  # VCP1 R115 - Molecular Haemostasis (Viapath)
        **CAPTURE_PANEL_DICT["vcp1"],
        **CONGENICA_CREDENTIALS["viapath"],
        "test_number": "R115",
        "congenica_project": 4699,
    },
    "Pan4976": {  # VCP1 R116 - Molecular Haemostasis (Viapath)
        **CAPTURE_PANEL_DICT["vcp1"],
        **CONGENICA_CREDENTIALS["viapath"],
        "test_number": "R116",
        "congenica_project": 4699,
    },
    "Pan4977": {  # VCP1 R117 - Molecular Haemostasis (Viapath)
        **CAPTURE_PANEL_DICT["vcp1"],
        **CONGENICA_CREDENTIALS["viapath"],
        "test_number": "R117",
        "congenica_project": 4699,
    },
    "Pan4978": {  # VCP1 R118 - Molecular Haemostasis (Viapath)
        **CAPTURE_PANEL_DICT["vcp1"],
        **CONGENICA_CREDENTIALS["viapath"],
        "test_number": "R118",
        "congenica_project": 4699,
    },
    "Pan4979": {  # VCP1 R119 - Molecular Haemostasis (Viapath)
        **CAPTURE_PANEL_DICT["vcp1"],
        **CONGENICA_CREDENTIALS["viapath"],
        "test_number": "R119",
        "congenica_project": 4699,
    },
    "Pan4980": {  # VCP1 R120 - Molecular Haemostasis (Viapath)
        **CAPTURE_PANEL_DICT["vcp1"],
        **CONGENICA_CREDENTIALS["viapath"],
        "test_number": "R120",
        "congenica_project": 4699,
    },
    "Pan4981": {  # VCP1 R121 - Molecular Haemostasis (Viapath)
        **CAPTURE_PANEL_DICT["vcp1"],
        **CONGENICA_CREDENTIALS["viapath"],
        "test_number": "R121",
        "congenica_project": 4699,
    },
    "Pan4982": {  # VCP1 R122 - Molecular Haemostasis (Viapath)
        **CAPTURE_PANEL_DICT["vcp1"],
        **CONGENICA_CREDENTIALS["viapath"],
        "test_number": "R122",
        "congenica_project": 4699,
    },
    "Pan4983": {  # VCP1 R123 - Molecular Haemostasis (Viapath)
        **CAPTURE_PANEL_DICT["vcp1"],
        **CONGENICA_CREDENTIALS["viapath"],
        "test_number": "R123",
        "congenica_project": 4699,
    },
    "Pan4984": {  # VCP1 R124 - Molecular Haemostasis (Viapath)
        **CAPTURE_PANEL_DICT["vcp1"],
        **CONGENICA_CREDENTIALS["viapath"],
        "test_number": "R124",
        "congenica_project": 4699,
    },
    "Pan4821": {  # VCP1 R13 - FH (STG)
        **CAPTURE_PANEL_DICT["vcp1"],
        **CONGENICA_CREDENTIALS["stg"],
        "test_number": "R13",
        "congenica_project": 4203,
        "FH": FH_PRS_BEDFILE,
    },
    "Pan4822": {  # VCP1 R184 - CF (STG)
        **CAPTURE_PANEL_DICT["vcp1"],
        **CONGENICA_CREDENTIALS["stg"],
        "test_number": "R184",
        "congenica_project": 4203,
    },
    "Pan4823": {  # VCP1 R25 - FGFR (STG)
        **CAPTURE_PANEL_DICT["vcp1"],
        **CONGENICA_CREDENTIALS["stg"],
        "test_number": "R25",
        "congenica_project": 4203,
    },
    "Pan4824": {  # VCP1 R73 - DMD (STG)
        **CAPTURE_PANEL_DICT["vcp1"],
        "test_number": "R73",
        "congenica_project": 4203,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
    },
    "Pan4825": {  # VCP1 R337 - cadasil (STG)
        **CAPTURE_PANEL_DICT["vcp1"],
        **CONGENICA_CREDENTIALS["stg"],
        "test_number": "R337",
        "congenica_project": 4203,
    },
    "Pan4149": {  # VCP2 R208 - BRCA (Viapath)
        **CAPTURE_PANEL_DICT["vcp2"],
        **CONGENICA_CREDENTIALS["viapath"],
        "test_number": "R208",
        "congenica_project": 4665,
    },
    "Pan4150": {  # VCP2 R207 - ovarian cancer (Viapath)
        **CAPTURE_PANEL_DICT["vcp2"],
        "test_number": "R207",
        "congenica_project": 4864,
        "congenica_credentials": "Viapath",
        "congenica_IR_template": "priority",
        "polyedge": POLYEDGE_INPUTS["MSH2"],
    },
    "Pan4127": {  # VCP2 R209 - colorectal cancer (Viapath)
        **CAPTURE_PANEL_DICT["vcp2"],
        "test_number": "R209",
        "congenica_project": 5093,
        "congenica_credentials": "Viapath",
        "congenica_IR_template": "priority",
    },
    "Pan4129": {  # VCP2 R210 - Lynch syndrome (Viapath)
        **CAPTURE_PANEL_DICT["vcp2"],
        "test_number": "R210",
        "congenica_project": 5094,
        "congenica_credentials": "Viapath",
        "congenica_IR_template": "priority",
        "polyedge": POLYEDGE_INPUTS["MSH2"],
    },
    "Pan4964": {  # VCP2 R259 - nijmegen breakage (Viapath)
        **CAPTURE_PANEL_DICT["vcp2"],
        "test_number": "R259",
        "congenica_project": 9118,
        "congenica_credentials": "Viapath",
        "congenica_IR_template": "priority",
    },
    "Pan4130": {  # VCP2 R211 - polyposis (Viapath)
        **CAPTURE_PANEL_DICT["vcp2"],
        "test_number": "R211",
        "congenica_project": 5095,
        "congenica_credentials": "Viapath",
        "congenica_IR_template": "priority",
        "polyedge": POLYEDGE_INPUTS["MSH2"],
    },
    "Pan5121": {  # VCP2 R430 prostate (Viapath)
        **CAPTURE_PANEL_DICT["vcp2"],
        "test_number": "R430",
        "congenica_project": 12814,
        "congenica_credentials": "Viapath",
        "congenica_IR_template": "priority",
        "polyedge": POLYEDGE_INPUTS["MSH2"],
    },
    "Pan4816": {  # VCP2 R208 - BRCA (STG)
        **CAPTURE_PANEL_DICT["vcp2"],
        "test_number": "R208",
        "congenica_project": 12915,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
    },
    "Pan4817": {  # VCP2 R207 - ovarian (STG)
        **CAPTURE_PANEL_DICT["vcp2"],
        "test_number": "R207",
        "congenica_project": 12914,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "polyedge": POLYEDGE_INPUTS["MSH2"],
    },
    "Pan4818": {  # VCP2 R209 - colorectal (STG)
        **CAPTURE_PANEL_DICT["vcp2"],
        "test_number": "R209",
        "congenica_project": 4202,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
    },
    "Pan5122": {  # VCP2 R430 - prostate (STG)
        **CAPTURE_PANEL_DICT["vcp2"],
        "test_number": "R430",
        "congenica_project": 12913,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "polyedge": POLYEDGE_INPUTS["MSH2"],
    },
    "Pan4819": {  # VCP2 R210 - lynch (STG)
        **CAPTURE_PANEL_DICT["vcp2"],
        "test_number": "R210",
        "congenica_project": 4202,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "polyedge": POLYEDGE_INPUTS["MSH2"],
    },
    "Pan4820": {  # VCP2 R211 - polyposis (STG)
        **CAPTURE_PANEL_DICT["vcp2"],
        "test_number": "R211",
        "congenica_project": 4202,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "polyedge": POLYEDGE_INPUTS["MSH2"],
    },
    "Pan4145": {  # VCP3 R79 - CMD (Viapath)
        **CAPTURE_PANEL_DICT["vcp3"],
        "test_number": "R79",
        "congenica_project": 4666,
        "congenica_credentials": "Viapath",
        "congenica_IR_template": "priority",
    },
    "Pan4146": {  # VCP3 R81 - CM (Viapath)
        **CAPTURE_PANEL_DICT["vcp3"],
        "test_number": "R81",
        "congenica_project": 4666,
        "congenica_credentials": "Viapath",
        "congenica_IR_template": "priority",
    },
    "Pan4132": {  # VCP3 R56 (Viapath)
        **CAPTURE_PANEL_DICT["vcp3"],
        "test_number": "R56",
        "congenica_project": 5092,
        "congenica_credentials": "Viapath",
        "congenica_IR_template": "priority",
    },
    "Pan4134": {  # VCP3 R57 (Viapath)
        **CAPTURE_PANEL_DICT["vcp3"],
        "test_number": "R57",
        "congenica_project": 5092,
        "congenica_credentials": "Viapath",
        "congenica_IR_template": "priority",
    },
    "Pan4136": {  # VCP3 R58 (Viapath)
        **CAPTURE_PANEL_DICT["vcp3"],
        "test_number": "R58",
        "congenica_project": 5092,
        "congenica_credentials": "Viapath",
        "congenica_IR_template": "priority",
    },
    "Pan4137": {  # VCP3 R60 (Viapath)
        **CAPTURE_PANEL_DICT["vcp3"],
        "test_number": "R60",
        "congenica_project": 5092,
        "congenica_credentials": "Viapath",
        "congenica_IR_template": "priority",
    },
    "Pan4138": {  # VCP3 R62 (Viapath)
        **CAPTURE_PANEL_DICT["vcp3"],
        "test_number": "R62",
        "congenica_project": 5092,
        "congenica_credentials": "Viapath",
        "congenica_IR_template": "priority",
    },
    "Pan4143": {  # VCP3 R66 (Viapath)
        **CAPTURE_PANEL_DICT["vcp3"],
        "test_number": "R66",
        "congenica_project": 5092,
        "congenica_credentials": "Viapath",
        "congenica_IR_template": "priority",
    },
    "Pan4144": {  # VCP3 R78 (Viapath)
        **CAPTURE_PANEL_DICT["vcp3"],
        "test_number": "R78",
        "congenica_project": 5092,
        "congenica_credentials": "Viapath",
        "congenica_IR_template": "priority",
    },
    "Pan4151": {  # VCP3 R82 - limb girdle (Viapath)
        **CAPTURE_PANEL_DICT["vcp3"],
        "test_number": "R82",
        "congenica_project": 5092,
        "congenica_credentials": "Viapath",
        "congenica_IR_template": "priority",
    },
    "Pan4314": {  # VCP3 R229 (Viapath)
        **CAPTURE_PANEL_DICT["vcp3"],
        "test_number": "R229",
        "congenica_project": 5290,
        "congenica_credentials": "Viapath",
        "congenica_IR_template": "priority",
    },
    "Pan4351": {  # VCP3 R227 (Viapath)
        **CAPTURE_PANEL_DICT["vcp3"],
        "test_number": "R227",
        "congenica_project": 5522,
        "congenica_credentials": "Viapath",
        "congenica_IR_template": "priority",
    },
    "Pan4387": {  # VCP3 R90 - Bleeding and platelet disorders (Viapath)
        **CAPTURE_PANEL_DICT["vcp3"],
        "test_number": "R90",
        "congenica_project": 4699,
        "congenica_credentials": "Viapath",
        "congenica_IR_template": "priority",
    },
    # VCP3 R97 - Thrombophilia with a likely monogenic cause (Viapath)
    "Pan4390": {
        **CAPTURE_PANEL_DICT["vcp3"],
        "test_number": "R97",
        "congenica_project": 4699,
        "congenica_credentials": "Viapath",
        "congenica_IR_template": "priority",
    },
    "Pan4826": {  # VCP3 R56 - (STG)
        **CAPTURE_PANEL_DICT["vcp3"],
        "test_number": "R56",
        "congenica_project": 4201,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
    },
    "Pan4827": {  # VCP3 R57 - (STG)
        **CAPTURE_PANEL_DICT["vcp3"],
        "test_number": "R57",
        "congenica_project": 4201,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
    },
    "Pan4828": {  # VCP3 R58 - (STG)
        **CAPTURE_PANEL_DICT["vcp3"],
        "test_number": "R58",
        "congenica_project": 4201,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
    },
    "Pan4829": {  # VCP3 R60 - (STG)
        **CAPTURE_PANEL_DICT["vcp3"],
        "test_number": "R60",
        "congenica_project": 4201,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
    },
    "Pan4830": {  # VCP3 R62 - (STG)
        **CAPTURE_PANEL_DICT["vcp3"],
        "test_number": "R62",
        "congenica_project": 4201,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
    },
    "Pan4831": {  # VCP3 R66 - (STG)
        **CAPTURE_PANEL_DICT["vcp3"],
        "test_number": "R66",
        "congenica_project": 4201,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
    },
    "Pan4832": {  # VCP3 R78 - (STG)
        **CAPTURE_PANEL_DICT["vcp3"],
        "test_number": "R78",
        "congenica_project": 4201,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
    },
    "Pan4833": {  # VCP3 R79 - CMD (STG)
        **CAPTURE_PANEL_DICT["vcp3"],
        "test_number": "R79",
        "congenica_project": 4201,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
    },
    "Pan4834": {  # VCP3 R81 - CM (STG)
        **CAPTURE_PANEL_DICT["vcp3"],
        "test_number": "R81",
        "congenica_project": 4201,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
    },
    "Pan4835": {  # VCP3 R82 - limb girdle (STG)
        **CAPTURE_PANEL_DICT["vcp3"],
        "test_number": "R82",
        "congenica_project": 4201,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
    },
    "Pan4836": {  # VCP3 R229 - (STG)
        **CAPTURE_PANEL_DICT["vcp3"],
        "test_number": "R229",
        "congenica_project": 4201,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
    },
}

# All panel numbers from PANEL_DICT
PANELS = list(PANEL_DICT.keys())

# Per-capture panel numbers
VCP_PANELS = {
    "vcp1": [k for k, v in PANEL_DICT.items() if v["panel_name"] == "vcp1"],
    "vcp2": [k for k, v in PANEL_DICT.items() if v["panel_name"] == "vcp2"],
    "vcp3": [k for k, v in PANEL_DICT.items() if v["panel_name"] == "vcp3"],
}

TSO500_PANELS = [k for k, v in PANEL_DICT.items() if v["pipeline"] == "tso500"]
WES_PANELS = [k for k, v in PANEL_DICT.items() if v["pipeline"] == "wes"]
SNP_PANELS = [k for k, v in PANEL_DICT.items() if v["pipeline"] == "snp"]
ARCHER_PANELS = [k for k, v in PANEL_DICT.items() if v["pipeline"] == "archerdx"]
SWIFT_57G_PANELS = [k for k, v in PANEL_DICT.items() if v["panel_name"] == "swift_57g"]
SWIFT_EGFR_PANELS = [
    k for k, v in PANEL_DICT.items() if v["panel_name"] == "swift_egfr"
]
LRPCR_PANELS = [k for k, v in PANEL_DICT.items() if v["panel_name"] == "lrpcr"]

# The below lists are used by the duty_csv app

# tso_pannumbers should not include the dry lab pan number as we do not want
# to include this as input to duty_csv as we do not want to download this to
# the trust network
TSO_VIAPATH_PANNUMBERS = [
    k
    for k, v in PANEL_DICT.items()
    if v["pipeline"] == "tso500" and v["dry_lab_only"] is False
]

STG_PANNUMBERS = [
    k
    for k, v in PANEL_DICT.items()
    if v["pipeline"] == "pipe" and v["congenica_credentials"] == "STG"
]

CP_CAPTURE_PANNOS = [
    CAPTURE_PANEL_DICT["vcp1"]["capture_pan_num"],
    CAPTURE_PANEL_DICT["vcp2"]["capture_pan_num"],
    CAPTURE_PANEL_DICT["vcp3"]["capture_pan_num"],
]
