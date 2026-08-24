export interface ImportColumnInspection {
  name: string
  sample_values: Array<string | number | boolean | null>
}

export interface ImportSheetInspection {
  name: string
  row_count: number
  columns: ImportColumnInspection[]
}

export interface ImportUploadResult {
  import_job_id: string
  status: string
  sheets: ImportSheetInspection[]
}
