# Logical Input Schema

Data kind: **catalogue**

Required logical fields:

- `source_id`
- `ra_deg`
- `dec_deg`
- `primary_measurements`
- `measurement_uncertainties`
- `quality_flags`
- `classification_or_group`
- `archive_version`

Map archive-specific names to these logical fields in a versioned configuration file. Fail clearly when a required field is absent.
