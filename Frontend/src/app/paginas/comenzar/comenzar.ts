import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-comenzar',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './comenzar.html',
  styleUrls: ['./comenzar.scss']
})
export class Comenzar {}
