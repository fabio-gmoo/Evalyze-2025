import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

// ✅ Renombrada: Evita chocar con tu interface Vacante del panel
export interface VacanteDTO {
  titulo: string;
  departamento: string;
  ubicacion: string;
  contrato: string;
  salarioMin: number;
  salarioMax: number;
  descripcion: string;
  requisitos: string;
  responsabilidades: string;
  duracionMin: number;
  puntajeMin: number;
  preguntas: { texto: string; tipo: string; peso: number; keywords: string }[];
}

@Injectable({ providedIn: 'root' })
export class VacanteService {
  private apiUrl = 'http://localhost:8000/vacantes/'; // ajusta si difiere

  constructor(private http: HttpClient) {}

  guardarvacante(vacante: VacanteDTO): Observable<any> {
    return this.http.post(`${this.apiUrl}/"guardar" `, vacante);
  }

  createVacante(vacante: VacanteDTO): Observable<any> {
    return this.http.post(`${this.apiUrl}/crear`, vacante);
  }

  editVacante(id: string, vacante: VacanteDTO): Observable<any> {
    return this.http.put(`${this.apiUrl}/editar/${id}`, vacante);
  }
}
