export interface Project {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at?: string;
}

export interface DatasetVersion {
  id: string;
  dataset_id: string;
  version_tag: string;
  format?: string;
  status: string;
  num_examples: number;
  created_at: string;
}

export interface Dataset {
  id: string;
  project_id: string;
  name: string;
  description?: string;
  created_at: string;
  versions: DatasetVersion[];
}

export interface TrainingJob {
  id: string;
  project_id: string;
  dataset_version_id: string;
  model_name: string;
  method: string;
  preset?: string;
  epochs: number;
  learning_rate: number;
  lora_rank: number;
  status: 'queued' | 'running' | 'completed' | 'failed' | 'cancel_requested' | 'cancelled';
  error_message?: string;
  current_step: number;
  total_steps: number;
  current_epoch: number;
  current_loss?: number;
  created_at: string;
  updated_at?: string;
}

export interface Experiment {
  id: string;
  project_id: string;
  training_job_id: string;
  model_id?: string;
  final_loss?: number;
  eval_loss?: number;
  metrics: Record<string, any>;
  created_at: string;
}

export interface Model {
  id: string;
  project_id: string;
  experiment_id: string;
  name: string;
  version: string;
  path: string;
  status: string;
  created_at: string;
}

export interface Evaluation {
  id: string;
  project_id: string;
  model_id: string;
  dataset_version_id: string;
  status: string;
  metrics: Record<string, any>;
  created_at: string;
}
