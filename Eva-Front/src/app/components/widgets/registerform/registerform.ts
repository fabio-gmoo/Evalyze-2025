import { Component, inject, signal, computed, effect } from '@angular/core';
import {
  ReactiveFormsModule,
  FormBuilder,
  Validators,
  AbstractControl,
  NonNullableFormBuilder,
} from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

type AccountType = 'company' | 'candidate';

@Component({
  selector: 'app-registerform',
  imports: [ReactiveFormsModule],
  templateUrl: './registerform.html',
  styleUrl: './registerform.scss',
})
export class Registerform {
  private fb = inject(FormBuilder);
  private http = inject(HttpClient);

  // UI
  showPw = signal(false);
  showCf = signal(false);
  loading = signal(false);
  errorMsg = signal<string | null>(null);

  // Tipo de cuenta (selector)
  accountType = signal<AccountType>('company');

  togglePw() {
    this.showPw.set(!this.showPw());
  }
  toggleCf() {
    this.showCf.set(!this.showCf());
  }
  setAccount(type: AccountType) {
    this.accountType.set(type);
  }

  form = this.fb.group(
    {
      // CANDIDATO
      name: ['', []], // requerido solo si candidate

      // EMPRESA
      company: ['', []], // requerido solo si company
      size: [''],
      role: [''],

      // COMÚN
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(6)]],
      confirm: ['', Validators.required],
      tos: [false, Validators.requiredTrue],
    },
    { validators: [match('password', 'confirm')] },
  );

  constructor() {
    // Reglas dinámicas según accountType
    effect(() => {
      const type = this.accountType();
      const nameCtrl = this.form.controls.name;
      const companyCtrl = this.form.controls.company;

      if (type === 'candidate') {
        nameCtrl.addValidators([Validators.required]);
        companyCtrl.clearValidators();
        companyCtrl.setValue('');
      } else {
        companyCtrl.addValidators([Validators.required]);
        nameCtrl.clearValidators();
        nameCtrl.setValue('');
      }
      nameCtrl.updateValueAndValidity({ emitEvent: false });
      companyCtrl.updateValueAndValidity({ emitEvent: false });
    });
  }

  async submit() {
    if (this.form.invalid || this.loading()) return;

    this.loading.set(true);
    this.errorMsg.set(null);

    const v = this.form.getRawValue();
    const type = this.accountType();

    // Endpoint + payload según tipo
    const url =
      type === 'company'
        ? 'http://localhost:8000/api/auth/register/company/'
        : 'http://localhost:8000/api/auth/register/candidate/';

    const payload =
      type === 'company'
        ? {
            email: v.email,
            password: v.password,
            confirm: v.confirm,
            company_name: v.company, // 👈 nombres que espera DRF
            size: v.size,
            industry: v.role, // si “role” = área/cargo
          }
        : {
            email: v.email,
            password: v.password,
            confirm: v.confirm,
            full_name: v.name, // 👈 nombres que espera DRF
          };

    try {
      await firstValueFrom(this.http.post(url, payload));
      // éxito: resetea y/o navega
      this.form.reset({ email: '', password: '', confirm: '', tos: false });
      this.accountType.set('company'); // opcional
      // TODO: router a login o mostrar toast
      console.log('SIGNUP OK', type, payload);
    } catch (err: any) {
      // Intenta mostrar mensaje de DRF amigable
      const e = err?.error;
      if (e && typeof e === 'object') {
        // Unifica errores de campos en una sola línea
        const msgs = Object.entries(e)
          .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
          .join(' · ');
        this.errorMsg.set(msgs || 'No se pudo completar el registro');
      } else {
        this.errorMsg.set('No se pudo completar el registro');
      }
    } finally {
      this.loading.set(false);
    }
  }
}

function match(a: string, b: string) {
  return (group: AbstractControl) => {
    const A = group.get(a)?.value,
      B = group.get(b)?.value;
    return A && B && A === B ? null : { mismatch: true };
  };
}
