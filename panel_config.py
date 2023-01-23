""" PANEL NUMBERS AND PANEL PROPERTIES

Need to test whether having these in this file will affect the trend analysis script
"""

# List of all panel numbers
panel_list = [
    "Pan4081",  # Swift EGFR
    "Pan4082",  # Swift 57
    "Pan2835",  # Twist WES
    "Pan4940",  # Twist WES for EB lab
    "Pan4119",  # VCP1 Viapath_R134(FH)
    "Pan4121",  # VCP1 Viapath_R184(CF)
    "Pan4122",  # VCP1 Viapath_R25(FGFR)
    "Pan4125",  # VCP1 Viapath_R73(DMD)
    "Pan4126",  # VCP1 Viapath_R337(CADASIL)
    "Pan4974",  # VCP1 Viapath (Molecular Haemostasis) R112
    "Pan4975",  # VCP1 Viapath (Molecular Haemostasis) R115
    "Pan4976",  # VCP1 Viapath (Molecular Haemostasis) R116
    "Pan4977",  # VCP1 Viapath (Molecular Haemostasis) R117
    "Pan4978",  # VCP1 Viapath (Molecular Haemostasis) R118
    "Pan4979",  # VCP1 Viapath (Molecular Haemostasis) R119
    "Pan4980",  # VCP1 Viapath (Molecular Haemostasis) R120
    "Pan4981",  # VCP1 Viapath (Molecular Haemostasis) R121
    "Pan4982",  # VCP1 Viapath (Molecular Haemostasis) R122
    "Pan4983",  # VCP1 Viapath (Molecular Haemostasis) R123
    "Pan4984",  # VCP1 Viapath (Molecular Haemostasis) R124
    "Pan4145",  # VCP3 Viapath_R79(CMD)
    "Pan4146",  # VCP3 Viapath_R81(CM)
    "Pan4149",  # VCP2 Viapath_R208(BRCA)
    "Pan4150",  # VCP2 Viapath_R207(ovarian)
    "Pan4127",  # VCP2 Viapath_R209(colorectal)
    "Pan4129",  # VCP2 Viapath_R210(lynch)
    "Pan4964",  # VCP2 Viapath_R259(nijmegen)
    "Pan4130",  # VCP2 Viapath_R211(polyposis)
    "Pan4132",  # VCP3 Viapath_R56
    "Pan4134",  # VCP3 Viapath_R57
    "Pan4136",  # VCP3 Viapath_R58
    "Pan4137",  # VCP3 Viapath_R60
    "Pan4138",  # VCP3 Viapath_R62
    "Pan4143",  # VCP3 Viapath_R66
    "Pan4144",  # VCP3 Viapath_R78
    "Pan4151",  # VCP3 Viapath_R82
    "Pan4314",  # VCP3 Viapath_R229
    "Pan4351",  # VCP3 Viapath_R227
    "Pan4387",  # VCP3 Viapath_R90
    "Pan4390",  # VCP3 Viapath_R97
    "Pan4009",  # MokaSNP
    "Pan4396",  # ArcherDx
    "Pan4579",  # VCP2_M1.1(somatic)
    "Pan4574",  # VCP2_M1.2(somatic)
    "Pan4969",  # TSO500 - no UTRS TERT promotor
    "Pan5085",  # TSO500 High throughput Synnovis. no UTRS TERT promotor
    "Pan5086",  # TSO500 High throughput BSPS. no UTRS TERT promotor
    "Pan4821",  # VCP1 STG R134_FH
    "Pan4822",  # VCP1 STG R184_CF
    "Pan4823",  # VCP1 STG R25_FGFR
    "Pan4824",  # VCP1 STG R73_DMD
    "Pan4825",  # VCP1 STG R337_CADASIL
    "Pan4816",  # VCP2 STG R208 BRCA
    "Pan4817",  # VCP2 STG R207 ovarian
    "Pan4818",  # VCP2 STG R209 colorectal
    "Pan4819",  # VCP2 STG R210 lynch
    "Pan4820",  # VCP2 STG R211 polyposis
    "Pan4826",  # VCP3 STG R56
    "Pan4827",  # VCP3 STG R57
    "Pan4828",  # VCP3 STG R58
    "Pan4829",  # VCP3 STG R60
    "Pan4830",  # VCP3 STG R62
    "Pan4831",  # VCP3 STG R66
    "Pan4832",  # VCP3 STG R78
    "Pan4833",  # VCP3 STG R79 CMD
    "Pan4834",  # VCP3 STG R81 CM
    "Pan4835",  # VCP3 STG R82 limb girdle
    "Pan4836",  # VCP3 STG R229
    "Pan5007",  # LRPCR Via R207 PMS2
    "Pan5008",  # LRPCR STG R207 PMS2
    "Pan5009",  # LRPCR Via R208 CHEK2
    "Pan5010",  # LRPCR STG R208 CHEK2
    "Pan5011",  # LRPCR Via R210 PMS2
    "Pan5012",  # LRPCR STG R210 PMS2
    "Pan5013",  # LRPCR Via R211 PMS2
    "Pan5014",  # LRPCR STG R211 PMS2
    "Pan5015",  # LRPCR Via R71 SMN1
    "Pan5016",  # LRPCR Via R239    IKBKG
]

# Per-capture panel numbers for use with RPKM
# IMPORTANT: Lists below are used by the trend analysis scripts.
# If changed, trend analysis script needs updating
vcp1_panel_list = ["Pan4119", "Pan4121", "Pan4122", "Pan4125", "Pan4126", "Pan4821",
                   "Pan4822", "Pan4823", "Pan4824", "Pan4825", "Pan4974", "Pan4975", "Pan4976",
                   "Pan4977", "Pan4978", "Pan4979", "Pan4980", "Pan4981", "Pan4982", "Pan4983",
                   "Pan4984"]
vcp2_panel_list = ["Pan4149", "Pan4150", "Pan4127", "Pan4129", "Pan4130",
                   "Pan4816", "Pan4817", "Pan4818", "Pan4819", "Pan4820", "Pan4964"]
vcp3_panel_list = ["Pan4132", "Pan4134", "Pan4136", "Pan4137", "Pan4138", "Pan4143", "Pan4144",
                   "Pan4145", "Pan4146", "Pan4151", "Pan4314", "Pan4351", "Pan4387",
                   "Pan4390", "Pan4826", "Pan4827", "Pan4828", "Pan4829", "Pan4830", "Pan4831",
                   "Pan4832", "Pan4833", "Pan4834", "Pan4835", "Pan4836"]
WES_panel_lists = ["Pan2835", "Pan4940"]
SNP_panel_lists = ["Pan4009"]
archer_panel_list = ["Pan4396"]
swift_57G_panel_list = ["Pan4082"]
swift_egfr_panel_list = ["Pan4081"]
mokacan_panel_list = ["Pan4579", "Pan4574"]
LRPCR_panel_list = ["Pan5007", "Pan5008", "Pan5009", "Pan5010", "Pan5011", "Pan5012", "Pan5013",
                    "Pan5014", "Pan5015", "Pan5016"]
# Settings from first item used when setting off dx run commands
tso500_panel_list = ["Pan4969", "Pan5085", "Pan5086"]


default_panel_properties = {
    "UMI": False,
    "UMI_bcl2fastq": None,  # E.g. Y145,I8,Y9I8,Y145
    "RPKM_bedfile_pan_number": None,
    "RPKM_also_analyse": None,  # List of Pan Numbers indicating which BAM files to download
    "mokawes": False,
    "joint_variant_calling": False,
    "mokaamp": False,
    "capture_type": "Hybridisation",  # "Amplicon" or "Hybridisation"
    "mokacan": False,
    "mokasnp": False,
    "mokapipe": False,
    "mokapipe_haplotype_caller_padding": 0,
    "FH": False,
    "FH_PRS_bedfile": "Pan4909.bed",  # Mokapipe FH_PRS BED file
    "mokaamp_varscan_strandfilter": True,
    "iva_upload": False,
    "congenica_upload": True,
    "STG": False,
    "oncology": False,
    "destination_command": None,
    "congenica_credentials": "Viapath",  # "Viapath" OR "STG"
    "congenica_IR_template": "priority",  # 'priority' or 'non-priority'
    "clinical_coverage_depth": None,  # Only found in mokamp command
    "multiqc_coverage_level": 30,
    "hsmetrics_bedfile": None,  # Only used when BED file name differs from Pan number
    "variant_calling_bedfile": None,  # Only used when BED file differs from Pan number
    "sambamba_bedfile": None,  # Only used when BED file differs from Pan number
    "mokaamp_bed_PE_input": None,  # Only used when BED file differs from Pan number
    "mokaamp_variant_calling_bed": None,  # Only used when BED file differs from Pan number
    "congenica_project": None,
    "peddy": False,
    "archerdx": False,
    "TSO500": False,
    "TSO500_high_throughput": False,
    "drylab_dnanexus_id": None,
    "masked_reference": False
}

# Override default panel settings
# masked_reference is currently set as hs37d5_Pan4967.bwa-index.tar.gz
panel_settings = {
    "Pan2835": {  # TWIST WES at GSTT
        "mokawes": True,
        "multiqc_coverage_level": 20,
        "hsmetrics_bedfile": "Twist_Exome_RefSeq_CCDS_v1.2_targets.bed",
        "sambamba_bedfile": "Pan493dataSambamba.bed",
        "peddy": True
    },
    "Pan4940": {  # TWIST WES for EB lab
        "mokawes": True,
        "multiqc_coverage_level": 20,
        "hsmetrics_bedfile": "Twist_Exome_RefSeq_CCDS_v1.2_targets.bed",
        "sambamba_bedfile": "Pan493dataSambamba.bed",
        "peddy": True,
        "congenica_project": "4697",
    },
    "Pan4081": {  # EGFR SWIFT Panel
        "mokaamp": True,
        "oncology": True,
        "capture_type": "Amplicon",
        "clinical_coverage_depth": 600,  # Only found in mokamp command
        "multiqc_coverage_level": 100,
        "hsmetrics_bedfile": "Pan4081.bed",
        "sambamba_bedfile": "Pan4081Sambamba.bed",
    },
    "Pan4082": {  # 57G SWIFT panel
        "mokaamp": True,
        "oncology": True,
        "capture_type": "Amplicon",
        "clinical_coverage_depth": 600,  # Only found in mokamp command
        "multiqc_coverage_level": 100,
        "hsmetrics_bedfile": "Pan4082.bed",
        "sambamba_bedfile": "Pan4082Sambamba.bed",
    },
    "Pan4009": {  # MokaSNP
        "mokasnp": True,
        "multiqc_coverage_level": 30,
        "variant_calling_bedfile": "Pan4009.bed",
    },
    "Pan4119": {  # VCP1 R134_Familial hypercholesterolaemia-Familial hypercholesterolaemia
                  # Small panel (Viapath)
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4399",
        "congenica_project": "4664",
        "RPKM_also_analyse": vcp1_panel_list,
        "hsmetrics_bedfile": "Pan4397data.bed",
        "sambamba_bedfile": "Pan4397dataSambamba.bed",
        "variant_calling_bedfile": "Pan4398data.bed",
        "FH": True,
    },
    "Pan4121": {  # VCP1 R184 CF (Viapath)
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4399",
        "congenica_project": "4862",
        "RPKM_also_analyse": vcp1_panel_list,
        "hsmetrics_bedfile": "Pan4397data.bed",
        "sambamba_bedfile": "Pan4397dataSambamba.bed",
        "variant_calling_bedfile": "Pan4398data.bed",
    },
    "Pan4122": {  # VCP1 R25 FGFR Viapath
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4399",
        "congenica_project": "5291",
        "RPKM_also_analyse": vcp1_panel_list,
        "hsmetrics_bedfile": "Pan4397data.bed",
        "sambamba_bedfile": "Pan4397dataSambamba.bed",
        "variant_calling_bedfile": "Pan4398data.bed",
    },
    "Pan4125": {  # VCP1 R73 DMD (Viapath)
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4399",
        "congenica_project": "4861",
        "RPKM_also_analyse": vcp1_panel_list,
        "hsmetrics_bedfile": "Pan4397data.bed",
        "sambamba_bedfile": "Pan4397dataSambamba.bed",
        "variant_calling_bedfile": "Pan4398data.bed",
    },
    "Pan4126": {  # VCP1 R337_CADASIL Viapath
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4399",
        "congenica_project": "4865",
        "RPKM_also_analyse": vcp1_panel_list,
        "hsmetrics_bedfile": "Pan4397data.bed",
        "sambamba_bedfile": "Pan4397dataSambamba.bed",
        "variant_calling_bedfile": "Pan4398data.bed",
    },
    "Pan4974": {  # VCP1 Viapath (Molecular Haemostasis) R112
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4399",
        "congenica_project": "4699",
        "RPKM_also_analyse": vcp1_panel_list,
        "hsmetrics_bedfile": "Pan4397data.bed",
        "sambamba_bedfile": "Pan4397dataSambamba.bed",
        "variant_calling_bedfile": "Pan4398data.bed",
    },
    "Pan4975": {  # VCP1 Viapath (Molecular Haemostasis) R115
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4399",
        "congenica_project": "4699",
        "RPKM_also_analyse": vcp1_panel_list,
        "hsmetrics_bedfile": "Pan4397data.bed",
        "sambamba_bedfile": "Pan4397dataSambamba.bed",
        "variant_calling_bedfile": "Pan4398data.bed",
    },
    "Pan4976": {  # VCP1 Viapath (Molecular Haemostasis) R116
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4399",
        "congenica_project": "4699",
        "RPKM_also_analyse": vcp1_panel_list,
        "hsmetrics_bedfile": "Pan4397data.bed",
        "sambamba_bedfile": "Pan4397dataSambamba.bed",
        "variant_calling_bedfile": "Pan4398data.bed",
    },
    "Pan4977": {  # VCP1 Viapath (Molecular Haemostasis) R117
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4399",
        "congenica_project": "4699",
        "RPKM_also_analyse": vcp1_panel_list,
        "hsmetrics_bedfile": "Pan4397data.bed",
        "sambamba_bedfile": "Pan4397dataSambamba.bed",
        "variant_calling_bedfile": "Pan4398data.bed",
    },
    "Pan4978": {  # VCP1 Viapath (Molecular Haemostasis) R118
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4399",
        "congenica_project": "4699",
        "RPKM_also_analyse": vcp1_panel_list,
        "hsmetrics_bedfile": "Pan4397data.bed",
        "sambamba_bedfile": "Pan4397dataSambamba.bed",
        "variant_calling_bedfile": "Pan4398data.bed",
    },
    "Pan4979": {  # VCP1 Viapath (Molecular Haemostasis) R119
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4399",
        "congenica_project": "4699",
        "RPKM_also_analyse": vcp1_panel_list,
        "hsmetrics_bedfile": "Pan4397data.bed",
        "sambamba_bedfile": "Pan4397dataSambamba.bed",
        "variant_calling_bedfile": "Pan4398data.bed",
    },
    "Pan4980": {  # VCP1 Viapath (Molecular Haemostasis) R120
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4399",
        "congenica_project": "4699",
        "RPKM_also_analyse": vcp1_panel_list,
        "hsmetrics_bedfile": "Pan4397data.bed",
        "sambamba_bedfile": "Pan4397dataSambamba.bed",
        "variant_calling_bedfile": "Pan4398data.bed",
    },
    "Pan4981": {  # VCP1 Viapath (Molecular Haemostasis) R121
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4399",
        "congenica_project": "4699",
        "RPKM_also_analyse": vcp1_panel_list,
        "hsmetrics_bedfile": "Pan4397data.bed",
        "sambamba_bedfile": "Pan4397dataSambamba.bed",
        "variant_calling_bedfile": "Pan4398data.bed",
    },
    "Pan4982": {  # VCP1 Viapath (Molecular Haemostasis) R122
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4399",
        "congenica_project": "4699",
        "RPKM_also_analyse": vcp1_panel_list,
        "hsmetrics_bedfile": "Pan4397data.bed",
        "sambamba_bedfile": "Pan4397dataSambamba.bed",
        "variant_calling_bedfile": "Pan4398data.bed",
    },
    "Pan4983": {  # VCP1 Viapath (Molecular Haemostasis) R123
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4399",
        "congenica_project": "4699",
        "RPKM_also_analyse": vcp1_panel_list,
        "hsmetrics_bedfile": "Pan4397data.bed",
        "sambamba_bedfile": "Pan4397dataSambamba.bed",
        "variant_calling_bedfile": "Pan4398data.bed",
    },
    "Pan4984": {  # VCP1 Viapath (Molecular Haemostasis) R124
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4399",
        "congenica_project": "4699",
        "RPKM_also_analyse": vcp1_panel_list,
        "hsmetrics_bedfile": "Pan4397data.bed",
        "sambamba_bedfile": "Pan4397dataSambamba.bed",
        "variant_calling_bedfile": "Pan4398data.bed",
    },
    "Pan4149": {  # VCP2 BRCA (Viapath)
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan3614",
        "congenica_project": "4665",
        "RPKM_also_analyse": vcp2_panel_list,
        "hsmetrics_bedfile": "Pan4949data.bed",
        "sambamba_bedfile": "Pan4949dataSambamba.bed",
        "variant_calling_bedfile": "Pan4948data.bed",
    },
    "Pan4964": {  # VCP2 R259 nijmegen breakage (Viapath)
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan3614",
        "congenica_project": "9118",
        "RPKM_also_analyse": vcp2_panel_list,
        "hsmetrics_bedfile": "Pan4949data.bed",
        "sambamba_bedfile": "Pan4949dataSambamba.bed",
        "variant_calling_bedfile": "Pan4948data.bed",
    },
    "Pan4150": {  # VCP2 R207 ovarian cancer (Viapath)
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan3614",
        "congenica_project": "4864",
        "RPKM_also_analyse": vcp2_panel_list,
        "hsmetrics_bedfile": "Pan4949data.bed",
        "sambamba_bedfile": "Pan4949dataSambamba.bed",
        "variant_calling_bedfile": "Pan4948data.bed",
    },
    "Pan4127": {  # VCP2 R209 colorectal cancer (Viapath)
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan3614",
        "congenica_project": "5093",
        "RPKM_also_analyse": vcp2_panel_list,
        "hsmetrics_bedfile": "Pan4949data.bed",
        "sambamba_bedfile": "Pan4949dataSambamba.bed",
        "variant_calling_bedfile": "Pan4948data.bed",
    },
    "Pan4129": {  # VCP2 R210 Lynch syndrome (Viapath)
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan3614",
        "congenica_project": "5094",
        "RPKM_also_analyse": vcp2_panel_list,
        "hsmetrics_bedfile": "Pan4949data.bed",
        "sambamba_bedfile": "Pan4949dataSambamba.bed",
        "variant_calling_bedfile": "Pan4948data.bed",
    },
    "Pan4130": {  # VCP2 R211 polyposis (Viapath)
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan3614",
        "congenica_project": "5095",
        "RPKM_also_analyse": vcp2_panel_list,
        "hsmetrics_bedfile": "Pan4949data.bed",
        "sambamba_bedfile": "Pan4949dataSambamba.bed",
        "variant_calling_bedfile": "Pan4948data.bed",
    },
    "Pan4132": {  # VCP3 R56 (Viapath)
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4362",
        "congenica_project": "5092",
        "RPKM_also_analyse": vcp3_panel_list,
        "hsmetrics_bedfile": "Pan4535data.bed",
        "sambamba_bedfile": "Pan4535dataSambamba.bed",
        "variant_calling_bedfile": "Pan4535data.bed",
    },
    "Pan4134": {  # VCP3 R57 (Viapath)
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4362",
        "congenica_project": "5092",
        "RPKM_also_analyse": vcp3_panel_list,
        "hsmetrics_bedfile": "Pan4535data.bed",
        "sambamba_bedfile": "Pan4535dataSambamba.bed",
        "variant_calling_bedfile": "Pan4535data.bed"
    },
    "Pan4136": {  # VCP3 R58 (Viapath)
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4362",
        "congenica_project": "5092",
        "RPKM_also_analyse": vcp3_panel_list,
        "hsmetrics_bedfile": "Pan4535data.bed",
        "sambamba_bedfile": "Pan4535dataSambamba.bed",
        "variant_calling_bedfile": "Pan4535data.bed",
    },
    "Pan4137": {  # VCP3 R60 (Viapath)
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4362",
        "congenica_project": "5092",
        "RPKM_also_analyse": vcp3_panel_list,
        "hsmetrics_bedfile": "Pan4535data.bed",
        "sambamba_bedfile": "Pan4535dataSambamba.bed",
        "variant_calling_bedfile": "Pan4535data.bed",
    },
    "Pan4138": {  # VCP3 R62 (Viapath)
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4362",
        "congenica_project": "5092",
        "RPKM_also_analyse": vcp3_panel_list,
        "hsmetrics_bedfile": "Pan4535data.bed",
        "sambamba_bedfile": "Pan4535dataSambamba.bed",
        "variant_calling_bedfile": "Pan4535data.bed",
    },
    "Pan4143": {  # VCP3 R66 (Viapath)
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4362",
        "congenica_project": "5092",
        "RPKM_also_analyse": vcp3_panel_list,
        "hsmetrics_bedfile": "Pan4535data.bed",
        "sambamba_bedfile": "Pan4535dataSambamba.bed",
        "variant_calling_bedfile": "Pan4535data.bed",
    },
    "Pan4144": {  # VCP3 R78 (Viapath)
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4362",
        "congenica_project": "5092",
        "RPKM_also_analyse": vcp3_panel_list,
        "hsmetrics_bedfile": "Pan4535data.bed",
        "sambamba_bedfile": "Pan4535dataSambamba.bed",
        "variant_calling_bedfile": "Pan4535data.bed",
    },
    "Pan4145": {  # VCP3 R79 - CMD (Viapath)
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4362",
        "congenica_project": "4666",
        "RPKM_also_analyse": vcp3_panel_list,
        "hsmetrics_bedfile": "Pan4535data.bed",
        "sambamba_bedfile": "Pan4535dataSambamba.bed",
        "variant_calling_bedfile": "Pan4535data.bed",
    },
    "Pan4146": {  # VCP3 R81 CM (Viapath)
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4362",
        "congenica_project": "4666",
        "RPKM_also_analyse": vcp3_panel_list,
        "hsmetrics_bedfile": "Pan4535data.bed",
        "sambamba_bedfile": "Pan4535dataSambamba.bed",
        "variant_calling_bedfile": "Pan4535data.bed",
    },
    "Pan4151": {  # VCP3 R82 limb girdle (Viapath)
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4362",
        "congenica_project": "5092",
        "RPKM_also_analyse": vcp3_panel_list,
        "hsmetrics_bedfile": "Pan4535data.bed",
        "sambamba_bedfile": "Pan4535dataSambamba.bed",
        "variant_calling_bedfile": "Pan4535data.bed",
    },
    "Pan4351": {  # VCP3 R227 (Viapath)
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4362",
        "congenica_project": "5522",
        "RPKM_also_analyse": vcp3_panel_list,
        "hsmetrics_bedfile": "Pan4535data.bed",
        "sambamba_bedfile": "Pan4535dataSambamba.bed",
        "variant_calling_bedfile": "Pan4535data.bed",
    },
    "Pan4387": {  # VCP3 R90 Bleeding and platelet disorders (Viapath)
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4362",
        "congenica_project": "4699",
        "RPKM_also_analyse": vcp3_panel_list,
        "hsmetrics_bedfile": "Pan4535data.bed",
        "sambamba_bedfile": "Pan4535dataSambamba.bed",
        "variant_calling_bedfile": "Pan4535data.bed",
    },
    "Pan4390": {  # VCP3 R97 Thrombophilia with a likely monogenic cause (Viapath)
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4362",
        "congenica_project": "4699",
        "RPKM_also_analyse": vcp3_panel_list,
        "hsmetrics_bedfile": "Pan4535data.bed",
        "sambamba_bedfile": "Pan4535dataSambamba.bed",
        "variant_calling_bedfile": "Pan4535data.bed",
    },
    "Pan4314": {  # VCP3 R229 (Viapath)
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4362",
        "congenica_project": "5290",
        "RPKM_also_analyse": vcp3_panel_list,
        "hsmetrics_bedfile": "Pan4535data.bed",
        "sambamba_bedfile": "Pan4535dataSambamba.bed",
        "variant_calling_bedfile": "Pan4535data.bed",
    },
    "Pan4396": {  # ArcherDx
        "archerdx": True,
        "congenica_upload": False,
    },
    "Pan4574": {  # Somatic VCP2 M1.2
        "mokacan": True,
        "congenica_upload": False,
        "variant_calling_bedfile": "Pan4577data.bed",
        "hsmetrics_bedfile": "Pan4949data.bed",
        "clinical_coverage_depth": 200,
    },
    "Pan4579": {  # Somatic VCP2 M1.1
        "mokacan": True,
        "congenica_upload": False,
        "variant_calling_bedfile": "Pan4578data.bed",
        "hsmetrics_bedfile": "Pan4949data.bed",
        "clinical_coverage_depth": 200,
    },
    "Pan4969": {  # TSO500 no UTRs. TERT promotor
                  # NOTE - TSO500 output parser settings are taken from the first pan number
                  # listed in tso500_panel_list
        "TSO500": True,
        "sambamba_bedfile": "Pan4969dataSambamba.bed",
        "clinical_coverage_depth": 100,
        "multiqc_coverage_level": 100,
        "coverage_min_basecall_qual": 25,
        "coverage_min_mapping_qual": 30,
    },
    "Pan5085": {  # TSO500 High throughput Synnovis. no UTRs. TERT promotor
                  # NOTE - TSO500 output parser settings are taken from the first pan number
                  # listed in tso500_panel_list
        "TSO500": True,
        "TSO500_high_throughput": True,
        "sambamba_bedfile": "Pan4969dataSambamba.bed",
        "clinical_coverage_depth": 100,
        "multiqc_coverage_level": 100,
        "coverage_min_basecall_qual": 25,
        "coverage_min_mapping_qual": 30,
    },
    "Pan5086": {  # TSO500 High throughput BSPS. no UTRs. TERT promotor
                  # NOTE - TSO500 output parser settings are taken from the first pan number
                  # listed in tso500_panel_list
        "TSO500": True,
        "TSO500_high_throughput": True,
        "sambamba_bedfile": "Pan4969dataSambamba.bed",
        "clinical_coverage_depth": 100,
        "multiqc_coverage_level": 100,
        "coverage_min_basecall_qual": 25,
        "coverage_min_mapping_qual": 30,
        "drylab_dnanexus_id": None  # Can state this when we know it.
    },
    "Pan4821": {  # VCP1 STG R134_FH
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4399",
        "RPKM_also_analyse": vcp1_panel_list,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "congenica_project": "4203",
        "hsmetrics_bedfile": "Pan4397data.bed",
        "variant_calling_bedfile": "Pan4398data.bed",
        "sambamba_bedfile": "Pan4397dataSambamba.bed",
        "STG": True,
        "FH": True,
    },
    "Pan4822": {  # VCP1 STG R184_CF
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4399",
        "RPKM_also_analyse": vcp1_panel_list,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "congenica_project": "4203",
        "hsmetrics_bedfile": "Pan4397data.bed",
        "variant_calling_bedfile": "Pan4398data.bed",
        "sambamba_bedfile": "Pan4397dataSambamba.bed",
        "STG": True,
    },
    "Pan4823": {  # VCP1 STG R25_FGFR
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4399",
        "RPKM_also_analyse": vcp1_panel_list,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "congenica_project": "4203",
        "hsmetrics_bedfile": "Pan4397data.bed",
        "variant_calling_bedfile": "Pan4398data.bed",
        "sambamba_bedfile": "Pan4397dataSambamba.bed",
        "STG": True,
    },
    "Pan4824": {  # VCP1 STG R73_DMD
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4399",
        "RPKM_also_analyse": vcp1_panel_list,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "congenica_project": "4203",
        "hsmetrics_bedfile": "Pan4397data.bed",
        "variant_calling_bedfile": "Pan4398data.bed",
        "sambamba_bedfile": "Pan4397dataSambamba.bed",
        "STG": True,
    },
    "Pan4825": {  # VCP1 STG R337_cadasil
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4399",
        "RPKM_also_analyse": vcp1_panel_list,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "congenica_project": "4203",
        "hsmetrics_bedfile": "Pan4397data.bed",
        "variant_calling_bedfile": "Pan4398data.bed",
        "sambamba_bedfile": "Pan4397dataSambamba.bed",
        "STG": True,
    },
    "Pan4826": {  # VCP3 STG R56
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan3974",
        "RPKM_also_analyse": vcp3_panel_list,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "congenica_project": "4201",
        "hsmetrics_bedfile": "Pan4535data.bed",
        "variant_calling_bedfile": "Pan4535data.bed",
        "sambamba_bedfile": "Pan4535dataSambamba.bed",
    },
    "Pan4827": {  # VCP3 STG R57
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan3974",
        "RPKM_also_analyse": vcp3_panel_list,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "congenica_project": "4201",
        "hsmetrics_bedfile": "Pan4535data.bed",
        "variant_calling_bedfile": "Pan4535data.bed",
        "sambamba_bedfile": "Pan4535dataSambamba.bed",
    },
    "Pan4828": {  # VCP3 STG R58
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan3974",
        "RPKM_also_analyse": vcp3_panel_list,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "congenica_project": "4201",
        "hsmetrics_bedfile": "Pan4535data.bed",
        "variant_calling_bedfile": "Pan4535data.bed",
        "sambamba_bedfile": "Pan4535dataSambamba.bed",
    },
    "Pan4829": {  # VCP3 STG R60
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan3974",
        "RPKM_also_analyse": vcp3_panel_list,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "congenica_project": "4201",
        "hsmetrics_bedfile": "Pan4535data.bed",
        "variant_calling_bedfile": "Pan4535data.bed",
        "sambamba_bedfile": "Pan4535dataSambamba.bed",
    },
    "Pan4830": {  # VCP3 STG R62
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan3974",
        "RPKM_also_analyse": vcp3_panel_list,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "congenica_project": "4201",
        "hsmetrics_bedfile": "Pan4535data.bed",
        "variant_calling_bedfile": "Pan4535data.bed",
        "sambamba_bedfile": "Pan4535dataSambamba.bed",
    },
    "Pan4831": {  # VCP3 STG R66
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan3974",
        "RPKM_also_analyse": vcp3_panel_list,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "congenica_project": "4201",
        "hsmetrics_bedfile": "Pan4535data.bed",
        "variant_calling_bedfile": "Pan4535data.bed",
        "sambamba_bedfile": "Pan4535dataSambamba.bed",
    },
    "Pan4832": {  # VCP3 STG R78
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan3974",
        "RPKM_also_analyse": vcp3_panel_list,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "congenica_project": "4201",
        "hsmetrics_bedfile": "Pan4535data.bed",
        "variant_calling_bedfile": "Pan4535data.bed",
        "sambamba_bedfile": "Pan4535dataSambamba.bed",
    },
    "Pan4833": {  # VCP3 STG R79
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan3974",
        "RPKM_also_analyse": vcp3_panel_list,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "congenica_project": "4201",
        "hsmetrics_bedfile": "Pan4535data.bed",
        "variant_calling_bedfile": "Pan4535data.bed",
        "sambamba_bedfile": "Pan4535dataSambamba.bed",
    },
    "Pan4834": {  # VCP3 STG R81
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan3974",
        "RPKM_also_analyse": vcp3_panel_list,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "congenica_project": "4201",
        "hsmetrics_bedfile": "Pan4535data.bed",
        "variant_calling_bedfile": "Pan4535data.bed",
        "sambamba_bedfile": "Pan4535dataSambamba.bed",
    },
    "Pan4835": {  # VCP3 STG R82
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan3974",
        "RPKM_also_analyse": vcp3_panel_list,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "congenica_project": "4201",
        "hsmetrics_bedfile": "Pan4535data.bed",
        "variant_calling_bedfile": "Pan4535data.bed",
        "sambamba_bedfile": "Pan4535dataSambamba.bed",
    },
    "Pan4836": {  # VCP3 STG R229
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan3974",
        "RPKM_also_analyse": vcp3_panel_list,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "congenica_project": "4201",
        "hsmetrics_bedfile": "Pan4535data.bed",
        "variant_calling_bedfile": "Pan4535data.bed",
        "sambamba_bedfile": "Pan4535dataSambamba.bed",
    },
    "Pan4818": {  # VCP2 STG R209
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan3614",
        "RPKM_also_analyse": vcp2_panel_list,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "congenica_project": "4202",
        "hsmetrics_bedfile": "Pan4949data.bed",
        "variant_calling_bedfile": "Pan4948data.bed",
        "sambamba_bedfile": "Pan4949dataSambamba.bed",
    },
    "Pan4819": {  # VCP2 STG R210
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan3614",
        "RPKM_also_analyse": vcp2_panel_list,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "congenica_project": "4202",
        "hsmetrics_bedfile": "Pan4949data.bed",
        "variant_calling_bedfile": "Pan4948data.bed",
        "sambamba_bedfile": "Pan4949dataSambamba.bed",
    },
    "Pan4820": {  # VCP2 STG R211
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan3614",
        "RPKM_also_analyse": vcp2_panel_list,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "congenica_project": "4202",
        "hsmetrics_bedfile": "Pan4949data.bed",
        "variant_calling_bedfile": "Pan4948data.bed",
        "sambamba_bedfile": "Pan4949dataSambamba.bed",
    },
    "Pan4816": {  # VCP2 STG R208
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan3614",
        "RPKM_also_analyse": vcp2_panel_list,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "congenica_project": "1099",
        "hsmetrics_bedfile": "Pan4949data.bed",
        "variant_calling_bedfile": "Pan4948data.bed",
        "sambamba_bedfile": "Pan4949dataSambamba.bed",
    },
    "Pan4817": {  # VCP2 STG R207
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan3614",
        "RPKM_also_analyse": vcp2_panel_list,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "congenica_project": "1099",
        "hsmetrics_bedfile": "Pan4949data.bed",
        "variant_calling_bedfile": "Pan4948data.bed",
        "sambamba_bedfile": "Pan4949dataSambamba.bed",
    },
    "Pan5007": {  # LRPCR Via R207 PMS2
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "capture_type": "Amplicon",
        "congenica_IR_template": "priority",
        "congenica_project": "9986",
        "hsmetrics_bedfile": "Pan4967_reference.bed",  # LRPCR amplicon BED file
        "variant_calling_bedfile": "Pan4767data.bed",
        "sambamba_bedfile": "Pan5018dataSambamba.bed",
        "masked_reference": "project-ByfFPz00jy1fk6PjpZ95F27J:file-GF84GF00QfBfzV35Gf8Qg53q"
    },
    "Pan5008": {  # LRPCR STG R207 PMS2
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "capture_type": "Amplicon",
        "congenica_IR_template": "non-priority",
        "congenica_project": "10010",
        "congenica_credentials": "STG",
        "hsmetrics_bedfile": "Pan4967_reference.bed",  # LRPCR amplicon BED file
        "variant_calling_bedfile": "Pan4767data.bed",
        "sambamba_bedfile": "Pan5018dataSambamba.bed",
        "masked_reference": "project-ByfFPz00jy1fk6PjpZ95F27J:file-GF84GF00QfBfzV35Gf8Qg53q"
    },
    "Pan5011": {  # LRPCR Via R210 PMS2
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "capture_type": "Amplicon",
        "congenica_IR_template": "priority",
        "congenica_project": "9981",
        "hsmetrics_bedfile": "Pan4967_reference.bed",  # LRPCR amplicon BED file
        "variant_calling_bedfile": "Pan4767data.bed",
        "sambamba_bedfile": "Pan5018dataSambamba.bed",
        "masked_reference": "project-ByfFPz00jy1fk6PjpZ95F27J:file-GF84GF00QfBfzV35Gf8Qg53q"
    },
    "Pan5012": {  # LRPCR STG R210 PMS2
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "capture_type": "Amplicon",
        "congenica_IR_template": "non-priority",
        "congenica_project": "10042",
        "congenica_credentials": "STG",
        "hsmetrics_bedfile": "Pan4967_reference.bed",  # LRPCR amplicon BED file
        "variant_calling_bedfile": "Pan4767data.bed",
        "sambamba_bedfile": "Pan5018dataSambamba.bed",
        "masked_reference": "project-ByfFPz00jy1fk6PjpZ95F27J:file-GF84GF00QfBfzV35Gf8Qg53q"
    },
    "Pan5013": {  # LRPCR Via R211 PMS2
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "capture_type": "Amplicon",
        "congenica_IR_template": "priority",
        "congenica_project": "9982",
        "hsmetrics_bedfile": "Pan4967_reference.bed",  # LRPCR amplicon BED file
        "variant_calling_bedfile": "Pan4767data.bed",
        "sambamba_bedfile": "Pan5018dataSambamba.bed",
        "masked_reference": "project-ByfFPz00jy1fk6PjpZ95F27J:file-GF84GF00QfBfzV35Gf8Qg53q"
    },
    "Pan5014": {  # LRPCR STG R211 PMS2
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "capture_type": "Amplicon",
        "congenica_IR_template": "non-priority",
        "congenica_project": "10042",
        "congenica_credentials": "STG",
        "hsmetrics_bedfile": "Pan4967_reference.bed",  # LRPCR amplicon BED file
        "variant_calling_bedfile": "Pan4767data.bed",
        "sambamba_bedfile": "Pan5018dataSambamba.bed",
        "masked_reference": "project-ByfFPz00jy1fk6PjpZ95F27J:file-GF84GF00QfBfzV35Gf8Qg53q"
    },
    "Pan5009": {  # LRPCR Via R208 CHEK2
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "capture_type": "Amplicon",
        "congenica_IR_template": "priority",
        "congenica_project": "9984",
        "hsmetrics_bedfile": "Pan4967_reference.bed",  # LRPCR amplicon BED file
        "variant_calling_bedfile": "Pan4767data.bed",
        "sambamba_bedfile": "Pan5018dataSambamba.bed",
        "masked_reference": "project-ByfFPz00jy1fk6PjpZ95F27J:file-GF84GF00QfBfzV35Gf8Qg53q"
    },
    "Pan5010": {  # LRPCR STG R208 CHEK2
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "capture_type": "Amplicon",
        "congenica_IR_template": "non-priority",
        "congenica_project": "10009",
        "congenica_credentials": "STG",
        "hsmetrics_bedfile": "Pan4967_reference.bed",  # LRPCR amplicon BED file
        "variant_calling_bedfile": "Pan4766data.bed",
        "sambamba_bedfile": "Pan5018dataSambamba.bed",
        "masked_reference": "project-ByfFPz00jy1fk6PjpZ95F27J:file-GF84GF00QfBfzV35Gf8Qg53q"
    },
    "Pan5015": {  # LRPCR Via R71 SMN1
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "capture_type": "Amplicon",
        "congenica_IR_template": "non-priority",  # TODO
        "congenica_project": "9547",  # TODO
        "hsmetrics_bedfile": "Pan4967_reference.bed",  # LRPCR amplicon BED file
        "variant_calling_bedfile": "Pan4971data.bed",
        "sambamba_bedfile": "Pan5018dataSambamba.bed",
        "masked_reference": "project-ByfFPz00jy1fk6PjpZ95F27J:file-GF84GF00QfBfzV35Gf8Qg53q"
    },
    "Pan5016": {  # LRPCR Via R239 IKBKG
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "capture_type": "Amplicon",
        "congenica_IR_template": "priority",
        "congenica_project": "9985",
        "hsmetrics_bedfile": "Pan4967_reference.bed",  # LRPCR amplicon BED file
        "variant_calling_bedfile": "Pan4768data.bed",
        "sambamba_bedfile": "Pan5018dataSambamba.bed",
        "masked_reference": "project-ByfFPz00jy1fk6PjpZ95F27J:file-GF84GF00QfBfzV35Gf8Qg53q"
    },
}
